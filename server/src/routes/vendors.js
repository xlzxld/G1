import { Router } from 'express';
import { db } from '../app.js';
import { authMiddleware } from '../middleware/auth.js';
import { requirePermission } from '../middleware/permissions.js';

const router = Router();
router.use(authMiddleware);
router.use(requirePermission('outsourcing', 'view'));

router.get('/', async (_req, res) => { res.json(await db('vendors').orderBy('name')); });

router.post('/', requirePermission('outsourcing', 'edit'), async (req, res) => {
  const { name, contact, phone, address, notes } = req.body;
  if (!name) return res.status(400).json({ error: 'Name required' });
  const [id] = await db('vendors').insert({ name, contact: contact || '', phone: phone || '', address: address || '', notes: notes || '' });
  res.status(201).json({ id, name });
});

router.put('/:id', requirePermission('outsourcing', 'edit'), async (req, res) => {
  const allowed = ['name', 'contact', 'phone', 'address', 'notes'];
  const updates = { updated_at: new Date().toISOString() };
  for (const k of allowed) { if (req.body[k] !== undefined) updates[k] = req.body[k]; }
  await db('vendors').where({ id: req.params.id }).update(updates);
  res.json({ updated: true });
});

router.delete('/:id', requirePermission('outsourcing', 'edit'), async (req, res) => {
  await db('vendors').where({ id: req.params.id }).del();
  res.json({ deleted: true });
});

export default router;
