import { Router } from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { db } from '../app.js';
import { authMiddleware } from '../middleware/auth.js';
import { requirePermission } from '../middleware/permissions.js';

const uploadDir = path.resolve('uploads');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });

const storage = multer.diskStorage({
  destination: (req, _file, cb) => {
    const { order_no } = req.params;
    const cat = req.body.category || '图纸';
    const dir = path.join(uploadDir, order_no, cat);
    fs.mkdirSync(dir, { recursive: true });
    cb(null, dir);
  },
  filename: (_req, file, cb) => {
    const ts = Date.now();
    cb(null, `v${ts}-${file.originalname}`);
  },
});
const upload = multer({ storage, limits: { fileSize: 50 * 1024 * 1024 } });

const router = Router();
router.use(authMiddleware);
router.use(requirePermission('drawings', 'view'));

router.get('/', async (req, res) => {
  const { order_id, category } = req.query;
  let q = db('documents').select('documents.*', 'orders.order_no').leftJoin('orders', 'documents.order_id', 'orders.id').orderBy('documents.created_at', 'desc');
  if (order_id) q = q.where('documents.order_id', order_id);
  if (category) q = q.where('documents.category', category);
  res.json(await q);
});

router.post('/upload/:order_no', requirePermission('drawings', 'edit'), upload.single('file'), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' });
  const order = await db('orders').where({ order_no: req.params.order_no }).first();
  if (!order) return res.status(404).json({ error: 'Order not found' });

  const category = req.body.category || '图纸';
  const last = await db('documents').where({ order_id: order.id, category }).orderBy('version', 'desc').first();
  const version = (last?.version || 0) + 1;

  // Deprecate previous versions in same category
  await db('documents').where({ order_id: order.id, category, status: 'active' }).update({ status: 'deprecated' });

  const [id] = await db('documents').insert({
    order_id: order.id, filename: req.file.filename, original_name: req.file.originalname,
    category, version, status: 'active',
    file_path: req.file.path, file_size: req.file.size, mime_type: req.file.mimetype,
    uploaded_by: req.user.id,
  });
  res.status(201).json({ id, version, filename: req.file.originalname, category });
});

router.put('/:id/status', requirePermission('drawings', 'edit'), async (req, res) => {
  const { status } = req.body;
  if (!['active', 'pending', 'deprecated'].includes(status)) return res.status(400).json({ error: 'Invalid status' });
  const doc = await db('documents').where({ id: req.params.id }).first();
  if (!doc) return res.status(404).json({ error: 'Not found' });

  if (status === 'active') {
    await db('documents').where({ order_id: doc.order_id, category: doc.category, status: 'active' }).whereNot({ id: doc.id }).update({ status: 'deprecated' });
  }
  await db('documents').where({ id: req.params.id }).update({ status });
  res.json({ updated: true });
});

router.delete('/:id', requirePermission('drawings', 'edit'), async (req, res) => {
  const doc = await db('documents').where({ id: req.params.id }).first();
  if (!doc) return res.status(404).json({ error: 'Not found' });
  try { fs.unlinkSync(doc.file_path); } catch {}
  await db('documents').where({ id: req.params.id }).del();
  res.json({ deleted: true });
});

export default router;
