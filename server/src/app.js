import 'dotenv/config';
import compression from 'compression';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const clientDist = path.resolve(__dirname, '..', '..', 'client', 'dist');
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
import settingsRoutes from './routes/settings.js';

export const db = knex(knexConfig);
export const refreshBlacklist = new Set();

const app = express();
app.use(compression());
app.use(cors());
app.use(express.static(clientDist, { maxAge: '7d', immutable: true }));
app.use(express.json({ limit: "50mb" }));
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
app.use('/api/settings', settingsRoutes);
app.get('/api/download/:order_no/:category/:filename', (req, res) => {
  const fp = path.resolve('uploads', decodeURIComponent(req.params.order_no), decodeURIComponent(req.params.category), decodeURIComponent(req.params.filename));
  res.sendFile(fp, (err) => { if (err) res.status(404).json({ error: 'File not found' }); });
});
app.get('/api/health', (_req, res) => res.json({ status: 'ok' }));

app.get('*', (_req, res) => res.sendFile(path.join(clientDist, 'index.html')));
const port = process.env.PORT || 3000;
async function start() {
  await db.migrate.latest(); console.log('Migrations up to date');
  const admin = await db('users').where({ username: 'admin' }).first();
  if (!admin) { await db.seed.run(); console.log('Seed data created'); }
  app.listen(port, () => console.log(`Server running on http://localhost:${port}`));
}
start().catch((err) => { console.error('Startup failed:', err); process.exit(1); });
