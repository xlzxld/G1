import { Router } from 'express';
import { db } from '../app.js';
import { authMiddleware } from '../middleware/auth.js';
import { requirePermission } from '../middleware/permissions.js';

const router = Router();
router.use(authMiddleware);
router.use(requirePermission('customers', 'view'));

router.get('/', async (req, res) => {
  const { keyword } = req.query;
  let q = db('customers').orderBy('updated_at', 'desc');
  if (keyword) q = q.where('name', 'like', `%${keyword}%`).orWhere('contact_methods', 'like', `%${keyword}%`);
  const rows = await q;
  res.json(rows);
});

router.post('/', requirePermission('customers', 'edit'), async (req, res) => {
  const { name, address, notes, contact_methods } = req.body;
  if (!name) return res.status(400).json({ error: 'Name required' });
  if (!contact_methods || !Array.isArray(contact_methods) || contact_methods.length === 0) {
    return res.status(400).json({ error: 'At least one contact method required' });
  }
  const [id] = await db('customers').insert({ name, address: address || '', notes: notes || '', contact_methods: JSON.stringify(contact_methods) });
  res.status(201).json({ id, name });
});

router.get('/:id', async (req, res) => {
  const cust = await db('customers').where({ id: req.params.id }).first();
  if (!cust) return res.status(404).json({ error: 'Not found' });
  res.json(cust);
});

router.put('/:id', requirePermission('customers', 'edit'), async (req, res) => {
  const allowed = ['name', 'address', 'notes'];
  const updates = { updated_at: new Date().toISOString() };
  for (const k of allowed) { if (req.body[k] !== undefined) updates[k] = req.body[k]; }
  if (req.body.contact_methods !== undefined) updates.contact_methods = JSON.stringify(req.body.contact_methods);
  await db('customers').where({ id: req.params.id }).update(updates);
  res.json({ updated: true });
});

router.delete('/:id', requirePermission('customers', 'edit'), async (req, res) => {
  await db('orders').where({ customer_id: req.params.id }).update({ customer_id: null });
  await db('customers').where({ id: req.params.id }).del();
  res.json({ deleted: true });
});

router.get('/:id/orders', async (req, res) => {
  const orders = await db('orders').where({ customer_id: req.params.id }).orderBy('created_at', 'desc');
  res.json(orders);
});

router.get('/:id/stats', async (req, res) => {
  const rows = await db('orders').where({ customer_id: req.params.id }).select('status').count('* as count').groupBy('status');
  const stats = { total: 0, completed: 0, in_progress: 0, paused: 0, aborted: 0 };
  for (const r of rows) { stats.total += r.count; if (r.status === 'completed') stats.completed += r.count; else if (r.status === 'paused' || r.status === 'aborted') stats[r.status] += r.count; else stats.in_progress += r.count; }
  res.json(stats);
});

export default router;
