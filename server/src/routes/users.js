import { Router } from 'express';
import bcrypt from 'bcryptjs';
import { db } from '../app.js';
import { authMiddleware, adminMiddleware } from '../middleware/auth.js';
import { requirePermission } from '../middleware/permissions.js';

const router = Router();
router.use(authMiddleware);
router.use(requirePermission('users', 'view'));

router.get('/', adminMiddleware, async (_req, res) => {
  const users = await db('users').select('id', 'username', 'display_name', 'role_label', 'is_admin', 'is_active', 'created_at');
  res.json(users);
});

router.post('/', adminMiddleware, requirePermission('users', 'edit'), async (req, res) => {
  const { username, display_name, role_label, password, is_admin, is_active } = req.body;
  if (!username || !password) {
    return res.status(400).json({ error: 'Username and password required' });
  }
  const existing = await db('users').where({ username }).first();
  if (existing) return res.status(409).json({ error: 'Username already exists' });
  const hash = await bcrypt.hash(password, 10);
  const [id] = await db('users').insert({
    username, display_name: display_name || username,
    role_label: role_label || '', password_hash: hash,
    is_admin: is_admin ? 1 : 0, is_active: is_active !== undefined ? (is_active ? 1 : 0) : 1,
  });
  res.status(201).json({ id, username });
});

router.put('/:id', adminMiddleware, requirePermission('users', 'edit'), async (req, res) => {
  const { id } = req.params;
  const user = await db('users').where({ id }).first();
  if (!user) return res.status(404).json({ error: 'User not found' });
  const updates = {};
  const allowed = ['display_name', 'role_label', 'is_admin', 'is_active', 'username'];
  for (const key of allowed) {
    if (req.body[key] !== undefined) updates[key] = req.body[key];
  }
  if (req.body.password) {
    updates.password_hash = await bcrypt.hash(req.body.password, 10);
  }
  if (Object.keys(updates).length === 0) {
    return res.status(400).json({ error: 'No valid fields to update' });
  }
  updates.updated_at = new Date().toISOString();
  await db('users').where({ id }).update(updates);
  res.json({ id: Number(id), updated: true });
});

router.delete('/:id', adminMiddleware, requirePermission('users', 'edit'), async (req, res) => {
  const { id } = req.params;
  const user = await db('users').where({ id }).first();
  if (!user) return res.status(404).json({ error: 'User not found' });
  if (user.is_admin) {
    const adminCount = await db('users').where({ is_admin: 1 }).count('* as count').first();
    if (adminCount.count <= 1) return res.status(400).json({ error: 'Cannot delete the last admin' });
  }
  await db('page_permissions').where({ user_id: id }).del();
  await db('users').where({ id }).del();
  res.json({ deleted: true });
});

router.get('/:id/permissions', adminMiddleware, async (req, res) => {
  const { id } = req.params;
  const perms = await db('page_permissions').where({ user_id: id });
  res.json(perms.map((p) => ({
    page_key: p.page_key, can_view: !!p.can_view, can_edit: !!p.can_edit,
  })));
});

router.put('/:id/permissions', adminMiddleware, requirePermission('users', 'edit'), async (req, res) => {
  const { id } = req.params;
  const { permissions } = req.body;
  if (!Array.isArray(permissions)) {
    return res.status(400).json({ error: 'permissions must be an array' });
  }
  await db.transaction(async (trx) => {
    for (const perm of permissions) {
      await trx('page_permissions')
        .insert({
          user_id: Number(id), page_key: perm.page_key,
          can_view: perm.can_view ? 1 : 0, can_edit: perm.can_edit ? 1 : 0,
        })
        .onConflict(['user_id', 'page_key'])
        .merge(['can_view', 'can_edit']);
    }
  });
  res.json({ updated: true });
});

export default router;
