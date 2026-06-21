export async function up(knex) {
  await knex.schema.createTable('customers', (t) => {
    t.increments('id').primary();
    t.text('name').notNullable();
    t.text('contact').defaultTo('');
    t.text('phone').defaultTo('');
    t.text('address').defaultTo('');
    t.text('wechat').defaultTo('');
    t.text('email').defaultTo('');
    t.text('notes').defaultTo('');
    t.text('created_at').notNullable().defaultTo(knex.fn.now());
    t.text('updated_at').notNullable().defaultTo(knex.fn.now());
  });

  await knex.schema.alterTable('orders', (t) => {
    t.integer('customer_id').nullable().references('id').inTable('customers').onDelete('SET NULL');
  });

  // Migrate existing customer_name to customers table
  const distinctNames = await knex('orders').distinct('customer_name').whereNotNull('customer_name').where('customer_name', '!=', '');
  for (const row of distinctNames) {
    const [custId] = await knex('customers').insert({ name: row.customer_name });
    await knex('orders').where({ customer_name: row.customer_name }).update({ customer_id: custId });
  }
}

export async function down(knex) {
  await knex.schema.alterTable('orders', (t) => { t.dropColumn('customer_id'); });
  await knex.schema.dropTableIfExists('customers');
}
