export function up(knex) {
  return knex.schema
    .createTable('users', (t) => {
      t.increments('id').primary();
      t.text('username').notNullable().unique();
      t.text('display_name').notNullable();
      t.text('role_label').notNullable().defaultTo('');
      t.text('password_hash').notNullable();
      t.integer('is_admin').notNullable().defaultTo(0);
      t.integer('is_active').notNullable().defaultTo(1);
      t.text('created_at').notNullable().defaultTo(knex.fn.now());
      t.text('updated_at').notNullable().defaultTo(knex.fn.now());
    })
    .createTable('page_permissions', (t) => {
      t.increments('id').primary();
      t.integer('user_id').notNullable().references('id').inTable('users').onDelete('CASCADE');
      t.text('page_key').notNullable();
      t.integer('can_view').notNullable().defaultTo(0);
      t.integer('can_edit').notNullable().defaultTo(0);
      t.unique(['user_id', 'page_key']);
    });
}

export function down(knex) {
  return knex.schema.dropTableIfExists('page_permissions').dropTableIfExists('users');
}
