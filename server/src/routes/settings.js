import { Router } from 'express';
import { db } from '../app.js';
import { authMiddleware, adminMiddleware } from '../middleware/auth.js';
import bcrypt from 'bcryptjs';

const router = Router();
router.use(authMiddleware);

// System settings
router.get('/', async (_req, res) => {
  res.json(await db('system_settings').orderBy('category'));
});

router.put('/', adminMiddleware, async (req, res) => {
  const { key, value } = req.body;
  if (!key) return res.status(400).json({ error: 'key required' });
  await db('system_settings').insert({ key, value: value || '' }).onConflict('key').merge(['value', 'updated_at']);
  res.json({ updated: true });
});

// Change own password
router.put('/change-password', async (req, res) => {
  const { current_password, new_password } = req.body;
  if (!current_password || !new_password) return res.status(400).json({ error: 'current_password and new_password required' });
  if (new_password.length < 6) return res.status(400).json({ error: 'Password must be at least 6 characters' });
  const user = await db('users').where({ id: req.user.id }).first();
  const match = await bcrypt.compare(current_password, user.password_hash);
  if (!match) return res.status(401).json({ error: 'Current password incorrect' });
  const hash = await bcrypt.hash(new_password, 10);
  await db('users').where({ id: req.user.id }).update({ password_hash: hash, updated_at: new Date().toISOString() });
  res.json({ updated: true });
});

// Audit logs
router.get('/audit-logs', adminMiddleware, async (req, res) => {
  const logs = await db('audit_logs').select('audit_logs.*', 'users.username', 'users.display_name').leftJoin('users', 'audit_logs.user_id', 'users.id').orderBy('created_at', 'desc').limit(100);
  res.json(logs);
});

export default router;
