import 'dotenv/config';
import path from 'path';
import express from 'express';
import cors from 'cors';
import knex from 'knex';
import knexConfig from '../knexfile.js';
import authRoutes from './routes/auth.js';
import userRoutes from './routes/users.js';
import processFlowRoutes from './routes/process-flows.js';
import orderRoutes from './routes/orders.js';
import customerRoutes from './routes/customers.js';
import dashboardRoutes from './routes/dashboard.js';
import documentRoutes from './routes/documents.js';
import inventoryRoutes from './routes/inventory.js';
import notificationRoutes from './routes/notifications.js';
import vendorRoutes from './routes/vendors.js';

export const db = knex(knexConfig);
export const refreshBlacklist = new Set();

const app = express();
app.use(cors());
app.use(express.json());

app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/process-flows', processFlowRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/customers', customerRoutes);
app.use('/api/dashboard', dashboardRoutes);
app.use('/api/documents', documentRoutes);
app.use('/api/inventory', inventoryRoutes);
app.use('/api/notifications', notificationRoutes);
app.use('/api/vendors', vendorRoutes);

app.get('/api/download/:order_no/:category/:filename', (req, res) => {
  const { order_no, category } = req.params;
  const filename = decodeURIComponent(req.params.filename);
  const fp = path.resolve('uploads', decodeURIComponent(order_no), decodeURIComponent(category), filename);
  res.sendFile(fp, (err) => { if (err) res.status(404).json({ error: 'File not found' }); });
});

app.get('/api/health', (_req, res) => res.json({ status: 'ok' }));

const port = process.env.PORT || 3000;

async function start() {
  await db.migrate.latest();
  console.log('Migrations up to date');
  const admin = await db('users').where({ username: 'admin' }).first();
  if (!admin) { await db.seed.run(); console.log('Seed data created'); }
  app.listen(port, () => console.log(`Server running on http://localhost:${port}`));
}

start().catch((err) => { console.error('Startup failed:', err); process.exit(1); });
