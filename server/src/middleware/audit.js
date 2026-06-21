import { db } from '../app.js';

const recentOps = new Map();

export function auditLog(action, entityType) {
  return (req, res, next) => {
    const origJson = res.json.bind(res);
    res.json = function (body) {
      const userId = req.user?.id || null;
      const entityId = req.params?.id ? Number(req.params.id) : (body?.id || null);
      const key = `${userId}-${action}-${entityType}-${entityId}`;
      const now = Date.now();
      if (!recentOps.has(key) || now - recentOps.get(key) > 1000) {
        recentOps.set(key, now);
        db('audit_logs').insert({
          user_id: userId, action, entity_type: entityType, entity_id: entityId,
          detail: `${req.method} ${req.originalUrl}`,
        }).catch(() => {});
        if (recentOps.size > 500) { const first = recentOps.keys().next().value; recentOps.delete(first); }
      }
      return origJson(body);
    };
    next();
  };
}
