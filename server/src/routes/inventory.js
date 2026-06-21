import { Router } from 'express';
import { db } from '../app.js';
import { authMiddleware } from '../middleware/auth.js';
import { requirePermission } from '../middleware/permissions.js';

const router = Router();
router.use(authMiddleware);
router.use(requirePermission('inventory', 'view'));

router.get('/', async (req, res) => {
  const items = await db('inventory_items').orderBy('updated_at', 'desc');
  res.json(items);
});

router.post('/', requirePermission('inventory', 'edit'), async (req, res) => {
  const { name, spec, total, unit, alert_threshold } = req.body;
  if (!name) return res.status(400).json({ error: 'Name required' });
  const [id] = await db('inventory_items').insert({ name, spec: spec || '', total: total || 0, unit: unit || '件', alert_threshold: alert_threshold || 5 });
  res.status(201).json({ id, name });
});

router.put('/:id', requirePermission('inventory', 'edit'), async (req, res) => {
  const allowed = ['name', 'spec', 'total', 'unit', 'alert_threshold'];
  const updates = { updated_at: new Date().toISOString() };
  for (const k of allowed) { if (req.body[k] !== undefined) updates[k] = req.body[k]; }
  await db('inventory_items').where({ id: req.params.id }).update(updates);
  res.json({ updated: true });
});

router.delete('/:id', requirePermission('inventory', 'edit'), async (req, res) => {
  await db('inventory_reservations').where({ item_id: req.params.id }).del();
  await db('inventory_items').where({ id: req.params.id }).del();
  res.json({ deleted: true });
});

router.get('/:id/reservations', async (req, res) => {
  const rows = await db('inventory_reservations').where({ item_id: req.params.id }).select('inventory_reservations.*', 'orders.order_no').leftJoin('orders', 'inventory_reservations.order_id', 'orders.id');
  res.json(rows);
});

router.post('/reserve', requirePermission('inventory', 'edit'), async (req, res) => {
  const { item_id, order_id, quantity } = req.body;
  if (!item_id || !order_id || !quantity) return res.status(400).json({ error: 'item_id, order_id, quantity required' });
  const item = await db('inventory_items').where({ id: item_id }).first();
  if (!item) return res.status(404).json({ error: 'Item not found' });
  const available = item.total - item.reserved;
  if (quantity > available) return res.status(400).json({ error: `库存不足：需要${quantity}，可用${available}` });
  await db.transaction(async (trx) => {
    await trx('inventory_items').where({ id: item_id }).increment('reserved', quantity);
    await trx('inventory_reservations').insert({ item_id, order_id, quantity });
  });
  res.status(201).json({ reserved: true });
});

router.delete('/reserve/:id', requirePermission('inventory', 'edit'), async (req, res) => {
  const r = await db('inventory_reservations').where({ id: req.params.id }).first();
  if (!r) return res.status(404).json({ error: 'Not found' });
  await db.transaction(async (trx) => {
    await trx('inventory_items').where({ id: r.item_id }).decrement('reserved', r.quantity);
    await trx('inventory_reservations').where({ id: req.params.id }).del();
  });
  res.json({ deleted: true });
});

export default router;
