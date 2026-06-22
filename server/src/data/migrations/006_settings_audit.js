export async function up(knex) {
  await knex.schema
    .createTable('system_settings', (t) => {
      t.increments('id').primary();
      t.text('key').notNullable().unique();
      t.text('value').notNullable();
      t.text('category').defaultTo('general');
      t.text('updated_at').notNullable().defaultTo(knex.fn.now());
    })
    .createTable('audit_logs', (t) => {
      t.increments('id').primary();
      t.integer('user_id').nullable().references('id').inTable('users').onDelete('SET NULL');
      t.text('action').notNullable();
      t.text('entity_type').notNullable();
      t.integer('entity_id').nullable();
      t.text('detail').defaultTo('');
      t.text('created_at').notNullable().defaultTo(knex.fn.now());
    });
}

export async function down(knex) {
  await knex.schema.dropTableIfExists('audit_logs').dropTableIfExists('system_settings');
}
