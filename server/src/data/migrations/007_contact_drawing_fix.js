export async function up(knex) {
  // Add contact_methods JSON field to customers
  await knex.schema.alterTable('customers', (t) => {
    t.text('contact_methods').defaultTo('[]');
  });
  // Migrate existing contact data to JSON
  const customers = await knex('customers').select('*');
  for (const c of customers) {
    const methods = [];
    if (c.contact) methods.push({ type: '联系人', value: c.contact });
    if (c.phone) methods.push({ type: '电话', value: c.phone });
    if (c.wechat) methods.push({ type: '微信', value: c.wechat });
    if (c.email) methods.push({ type: '邮箱', value: c.email });
    await knex('customers').where({ id: c.id }).update({ contact_methods: JSON.stringify(methods) });
  }
  // Add title/description to documents
  await knex.schema.alterTable('documents', (t) => {
    t.text('title').defaultTo('');
    t.text('description').defaultTo('');
  });
}

export async function down(knex) {
  await knex.schema.alterTable('documents', (t) => { t.dropColumn('title'); t.dropColumn('description'); });
  await knex.schema.alterTable('customers', (t) => { t.dropColumn('contact_methods'); });
}
