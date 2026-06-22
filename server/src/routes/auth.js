import { Router } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { db, refreshBlacklist } from '../app.js';
import { authMiddleware } from '../middleware/auth.js';

const router = Router();

router.post('/login', async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ error: 'Username and password required' });
  }
  const user = await db('users').where({ username }).first();
  if (!user || !user.is_active) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  const match = await bcrypt.compare(password, user.password_hash);
  if (!match) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  const payload = {
    id: user.id,
    username: user.username,
    display_name: user.display_name,
    is_admin: !!user.is_admin,
  };
  const accessToken = jwt.sign(payload, process.env.JWT_SECRET, {
    expiresIn: process.env.JWT_ACCESS_EXPIRES || '15m',
  });
  const refreshToken = jwt.sign(
    { id: user.id, type: 'refresh' },
    process.env.JWT_REFRESH_SECRET,
    { expiresIn: process.env.JWT_REFRESH_EXPIRES || '7d' }
  );
  res.json({ access_token: accessToken, refresh_token: refreshToken, user: payload });
});

router.post('/refresh', async (req, res) => {
  const { refresh_token } = req.body;
  if (!refresh_token) {
    return res.status(400).json({ error: 'Refresh token required' });
  }
  if (refreshBlacklist.has(refresh_token)) {
    return res.status(401).json({ error: 'Token revoked' });
  }
  try {
    const payload = jwt.verify(refresh_token, process.env.JWT_REFRESH_SECRET);
    if (payload.type !== 'refresh') throw new Error();
    const user = await db('users').where({ id: payload.id }).first();
    if (!user || !user.is_active) {
      return res.status(401).json({ error: 'User not found or inactive' });
    }
    const accessPayload = {
      id: user.id,
      username: user.username,
      display_name: user.display_name,
      is_admin: !!user.is_admin,
    };
    const accessToken = jwt.sign(accessPayload, process.env.JWT_SECRET, {
      expiresIn: process.env.JWT_ACCESS_EXPIRES || '15m',
    });
    res.json({ access_token: accessToken });
  } catch {
    return res.status(401).json({ error: 'Invalid refresh token' });
  }
});

router.post('/logout', authMiddleware, (req, res) => {
  const { refresh_token } = req.body;
  if (refresh_token) {
    refreshBlacklist.add(refresh_token);
  }
  res.json({ message: 'Logged out' });
});

router.get('/me', authMiddleware, async (req, res) => {
  const user = await db('users').where({ id: req.user.id }).first();
  if (!user) return res.status(404).json({ error: 'User not found' });
  const permissions = await db('page_permissions').where({ user_id: user.id });
  res.json({
    id: user.id,
    username: user.username,
    display_name: user.display_name,
    role_label: user.role_label,
    is_admin: !!user.is_admin,
    permissions: permissions.map((p) => ({
      page_key: p.page_key,
      can_view: !!p.can_view,
      can_edit: !!p.can_edit,
    })),
  });
});

export default router;
