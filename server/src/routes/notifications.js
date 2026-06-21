import { Router } from 'express';
import { db } from '../app.js';
import { authMiddleware, adminMiddleware } from '../middleware/auth.js';

const router = Router();
router.use(authMiddleware);

router.get('/', async (req, res) => {
  const rows = await db('notifications').where({ to_user_id: req.user.id }).orderBy('created_at', 'desc').limit(50);
  res.json(rows);
});

router.get('/unread-count', async (req, res) => {
  const count = await db('notifications').where({ to_user_id: req.user.id, is_read: 0 }).count('* as count').first();
  res.json({ count: count.count });
});

router.post('/', async (req, res) => {
  const { to_user_id, title, body, link } = req.body;
  if (!to_user_id || !title) return res.status(400).json({ error: 'to_user_id and title required' });
  const [id] = await db('notifications').insert({ from_user_id: req.user.id, to_user_id, title, body: body || '', link: link || '', source: 'manual' });
  res.status(201).json({ id });
});

router.put('/:id/read', async (req, res) => {
  await db('notifications').where({ id: req.params.id, to_user_id: req.user.id }).update({ is_read: 1 });
  res.json({ updated: true });
});

router.put('/read-all', async (req, res) => {
  await db('notifications').where({ to_user_id: req.user.id, is_read: 0 }).update({ is_read: 1 });
  res.json({ updated: true });
});

router.get('/rules', adminMiddleware, async (_req, res) => {
  res.json(await db('notification_rules').orderBy('created_at', 'desc'));
});

router.post('/rules', adminMiddleware, async (req, res) => {
  const { name, event, condition_field, condition_op, condition_value, notify_role, title_template, body_template } = req.body;
  if (!name || !event || !title_template) return res.status(400).json({ error: 'name, event, title_template required' });
  const [id] = await db('notification_rules').insert({ name, event, condition_field, condition_op, condition_value, notify_role, title_template, body_template });
  res.status(201).json({ id });
});

router.put('/rules/:id', adminMiddleware, async (req, res) => {
  const { is_active } = req.body;
  await db('notification_rules').where({ id: req.params.id }).update({ is_active: is_active ? 1 : 0 });
  res.json({ updated: true });
});

router.delete('/rules/:id', adminMiddleware, async (req, res) => {
  await db('notification_rules').where({ id: req.params.id }).del();
  res.json({ deleted: true });
});

export default router;
