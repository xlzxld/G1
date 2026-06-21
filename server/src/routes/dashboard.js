import { Router } from 'express';
import { db } from '../app.js';
import { authMiddleware } from '../middleware/auth.js';

const router = Router();
router.use(authMiddleware);

router.get('/stats', async (req, res) => {
  const now = new Date().toISOString().slice(0, 10);
  const [todayOrders, inProgress, customerConfirm, inventory, todayDone, recentCustomers, myTodos] = await Promise.all([
    db('orders').where({ status: 'draft' }).orWhereNull('customer_id').count('* as count').first(),
    db('orders').whereNotIn('status', ['completed', 'paused', 'aborted', 'draft']).count('* as count').first(),
    db('orders').where({ status: 'customer_confirm' }).count('* as count').first(),
    db('orders').whereNotNull('customer_id').count('* as count').first(),
    db('orders').where({ status: 'completed' }).where('updated_at', 'like', `${now}%`).count('* as count').first(),
    db('customers').orderBy('created_at', 'desc').limit(5),
    db('process_steps').where({ assignee: req.user.username, status: 'pending' }).count('* as count').first(),
  ]);
  res.json({
    today_pending: todayOrders.count || 0,
    in_progress: inProgress.count || 0,
    customer_confirm: customerConfirm.count || 0,
    inventory_alert: 0,
    today_done: todayDone.count || 0,
    recent_customers: recentCustomers,
    my_todos: myTodos.count || 0,
  });
});

export default router;
