export default {
  client: 'better-sqlite3',
  connection: { filename: './data/mes.db' },
  useNullAsDefault: true,
  migrations: { directory: './src/data/migrations' },
  seeds: { directory: './src/data/seeds' },
};
