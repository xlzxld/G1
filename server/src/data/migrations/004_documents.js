export async function up(knex) {
  await knex.schema.createTable('documents', (t) => {
    t.increments('id').primary();
    t.integer('order_id').notNullable().references('id').inTable('orders').onDelete('CASCADE');
    t.text('filename').notNullable();
    t.text('original_name').notNullable();
    t.text('category').notNullable().defaultTo('图纸');
    t.integer('version').notNullable().defaultTo(1);
    t.text('status').notNullable().defaultTo('active');
    t.text('file_path').notNullable();
    t.integer('file_size').defaultTo(0);
    t.text('mime_type').defaultTo('');
    t.integer('uploaded_by').nullable().references('id').inTable('users').onDelete('SET NULL');
    t.text('created_at').notNullable().defaultTo(knex.fn.now());
  });
}

export async function down(knex) {
  await knex.schema.dropTableIfExists('documents');
}
