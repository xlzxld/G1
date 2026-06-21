import { Router } from 'express';
import { db } from '../app.js';
import { authMiddleware } from '../middleware/auth.js';
import { requirePermission } from '../middleware/permissions.js';

const router = Router();
router.use(authMiddleware);
router.use(requirePermission('process_flow', 'view'));

router.get('/', async (_req, res) => {
  const flows = await db('process_flows').where({ is_template: 1 }).orderBy('updated_at', 'desc');
  res.json(flows);
});

router.post('/', requirePermission('process_flow', 'edit'), async (req, res) => {
  const { name, description } = req.body;
  if (!name) return res.status(400).json({ error: 'Name required' });
  const [id] = await db('process_flows').insert({ name, description: description || '', is_template: 1 });
  res.status(201).json({ id, name });
});

router.get('/:id', async (req, res) => {
  const flow = await db('process_flows').where({ id: req.params.id }).first();
  if (!flow) return res.status(404).json({ error: 'Not found' });
  const steps = await db('process_steps').where({ flow_id: flow.id }).orderBy('seq', 'asc');
  res.json({ ...flow, steps });
});

router.put('/:id', requirePermission('process_flow', 'edit'), async (req, res) => {
  const { name, description } = req.body;
  const updates = { updated_at: new Date().toISOString() };
  if (name !== undefined) updates.name = name;
  if (description !== undefined) updates.description = description;
  await db('process_flows').where({ id: req.params.id }).update(updates);
  res.json({ updated: true });
});

router.delete('/:id', requirePermission('process_flow', 'edit'), async (req, res) => {
  await db('process_steps').where({ flow_id: req.params.id }).del();
  await db('process_flows').where({ id: req.params.id }).del();
  res.json({ deleted: true });
});

router.put('/:id/steps', requirePermission('process_flow', 'edit'), async (req, res) => {
  const { steps } = req.body;
  if (!Array.isArray(steps)) return res.status(400).json({ error: 'steps must be an array' });
  const flowId = Number(req.params.id);
  await db.transaction(async (trx) => {
    await trx('process_steps').where({ flow_id: flowId }).del();
    for (const s of steps) {
      await trx('process_steps').insert({
        flow_id: flowId, name: s.name, seq: s.seq, required: s.required ? 1 : 0,
        can_parallel: s.can_parallel ? 1 : 0,
        depends_on_step_id: s.depends_on_step_id || null,
        assignee: s.assignee || '',
        completion_condition: s.completion_condition || 'manual',
        outsourced: s.outsourced ? 1 : 0,
        status: 'pending',
      });
    }
  });
  res.json({ updated: true });
});

router.post('/:id/steps', requirePermission('process_flow', 'edit'), async (req, res) => {
  const { name, seq, required, can_parallel, assignee, completion_condition } = req.body;
  if (!name) return res.status(400).json({ error: 'Name required' });
  const max = await db('process_steps').where({ flow_id: req.params.id }).max('seq as m').first();
  const [id] = await db('process_steps').insert({
    flow_id: Number(req.params.id), name, seq: seq !== undefined ? seq : (max?.m || 0) + 1,
    required: required !== undefined ? (required ? 1 : 0) : 1,
    can_parallel: can_parallel ? 1 : 0,
    assignee: assignee || '', completion_condition: completion_condition || 'manual',
    status: 'pending',
  });
  res.status(201).json({ id, name });
});

export default router;
