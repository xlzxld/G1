import { Router } from 'express';
import { db } from '../app.js';
import { authMiddleware, adminMiddleware } from '../middleware/auth.js';
import { requirePermission } from '../middleware/permissions.js';
import { advanceStep, rollbackStep, skipStep, copyFlowToOrder } from '../services/processEngine.js';

const router = Router();
router.use(authMiddleware);
router.use(requirePermission('orders', 'view'));

router.get('/', async (req, res) => {
  const { keyword, status, customer_name, priority, sort_by, sort_order, page, limit } = req.query;
  let q = db('orders').select('orders.*', 'ps.name as current_step_name').leftJoin('process_steps as ps', 'orders.current_step_id', 'ps.id');
  if (keyword) q = q.where(function () { this.where('order_no', 'like', `%${keyword}%`).orWhere('product_name', 'like', `%${keyword}%`).orWhere('customer_name', 'like', `%${keyword}%`); });
  if (status) q = q.where('orders.status', status);
  if (customer_name) q = q.where('orders.customer_name', 'like', `%${customer_name}%`);
  if (priority !== undefined) q = q.where('orders.priority', priority);
  const countQ = q.clone().count('* as total').first();
  const col = sort_by || 'created_at';
  const dir = sort_order === 'asc' ? 'asc' : 'desc';
  q = q.orderBy(`orders.${col}`, dir);
  const pg = Math.max(1, parseInt(page) || 1);
  const lm = Math.min(100, parseInt(limit) || 20);
  q = q.offset((pg - 1) * lm).limit(lm);
  const [rows, countResult] = await Promise.all([q, countQ]);
  res.json({ data: rows, total: countResult.total, page: pg, limit: lm });
});

router.post('/', requirePermission('orders', 'edit'), async (req, res) => {
  const { template_flow_id, order_no, product_name, customer_name, priority, shipment_date, notes } = req.body;
  if (!order_no || !product_name) return res.status(400).json({ error: 'order_no and product_name required' });
  const existing = await db('orders').where({ order_no }).first();
  if (existing) return res.status(409).json({ error: 'Order number already exists' });
  const [orderId] = await db('orders').insert({
    order_no, product_name, customer_name: customer_name || '',
    priority: priority || 0, status: 'draft',
    shipment_date: shipment_date || null, notes: notes || '',
    created_by: req.user.id,
  });
  if (template_flow_id) {
    await copyFlowToOrder(Number(template_flow_id), orderId);
  }
  res.status(201).json({ id: orderId, order_no });
});

router.get('/:id', async (req, res) => {
  const order = await db('orders').where({ id: req.params.id }).first();
  if (!order) return res.status(404).json({ error: 'Not found' });
  const flow = await db('process_flows').where({ order_id: order.id, is_template: 0 }).first();
  let steps = [];
  if (flow) steps = await db('process_steps').where({ flow_id: flow.id }).orderBy('seq', 'asc');
  res.json({ ...order, flow_id: flow?.id, steps });
});

router.put('/:id', requirePermission('orders', 'edit'), async (req, res) => {
  const updates = { updated_at: new Date().toISOString() };
  const allowed = ['product_name', 'customer_name', 'priority', 'shipment_date', 'notes'];
  for (const k of allowed) { if (req.body[k] !== undefined) updates[k] = req.body[k]; }
  await db('orders').where({ id: req.params.id }).update(updates);
  res.json({ updated: true });
});

router.delete('/:id', requirePermission('orders', 'edit'), async (req, res) => {
  const order = await db('orders').where({ id: req.params.id }).first();
  if (!order) return res.status(404).json({ error: 'Not found' });
  // Cascade: delete flow + steps via process_steps FK + process_flows FK
  await db('process_flows').where({ order_id: order.id }).del();
  await db('orders').where({ id: order.id }).del();
  res.json({ deleted: true });
});

router.put('/:id/status', adminMiddleware, async (req, res) => {
  const { status } = req.body;
  if (!status) return res.status(400).json({ error: 'Status required' });
  await db('orders').where({ id: req.params.id }).update({ status, updated_at: new Date().toISOString() });
  res.json({ updated: true });
});

router.post('/:id/steps/:stepId/advance', requirePermission('orders', 'edit'), async (req, res) => {
  try {
    const result = await advanceStep(Number(req.params.stepId), req.user.id);
    res.json(result);
  } catch (e) { res.status(400).json({ error: e.message }); }
});

router.post('/:id/steps/:stepId/rollback', requirePermission('orders', 'edit'), async (req, res) => {
  try {
    const result = await rollbackStep(Number(req.params.stepId), req.user.id);
    res.json(result);
  } catch (e) { res.status(400).json({ error: e.message }); }
});

router.post('/:id/steps/:stepId/skip', requirePermission('orders', 'edit'), async (req, res) => {
  try {
    const result = await skipStep(Number(req.params.stepId), req.user.id);
    res.json(result);
  } catch (e) { res.status(400).json({ error: e.message }); }
});

export default router;
