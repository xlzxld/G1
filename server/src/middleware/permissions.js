import { db } from '../app.js';

export function requirePermission(pageKey, action = 'view') {
  return async (req, res, next) => {
    if (req.user.is_admin) return next();
    const perm = await db('page_permissions')
      .where({ user_id: req.user.id, page_key: pageKey })
      .first();
    if (!perm || !perm.can_view) {
      return res.status(403).json({ error: 'Forbidden: page not accessible' });
    }
    if (action === 'edit' && !perm.can_edit) {
      return res.status(403).json({ error: 'Forbidden: edit not allowed' });
    }
    next();
  };
}
