export async function up(knex) {
  await knex.schema
    .createTable('inventory_items', (t) => {
      t.increments('id').primary();
      t.text('name').notNullable();
      t.text('spec').defaultTo('');
      t.integer('total').notNullable().defaultTo(0);
      t.integer('reserved').notNullable().defaultTo(0);
      t.text('unit').defaultTo('件');
      t.integer('alert_threshold').defaultTo(5);
      t.text('created_at').notNullable().defaultTo(knex.fn.now());
      t.text('updated_at').notNullable().defaultTo(knex.fn.now());
    })
    .createTable('inventory_reservations', (t) => {
      t.increments('id').primary();
      t.integer('item_id').notNullable().references('id').inTable('inventory_items').onDelete('CASCADE');
      t.integer('order_id').notNullable().references('id').inTable('orders').onDelete('CASCADE');
      t.integer('quantity').notNullable().defaultTo(0);
      t.text('created_at').notNullable().defaultTo(knex.fn.now());
    })
    .createTable('notifications', (t) => {
      t.increments('id').primary();
      t.integer('from_user_id').nullable().references('id').inTable('users').onDelete('SET NULL');
      t.integer('to_user_id').notNullable().references('id').inTable('users').onDelete('CASCADE');
      t.text('title').notNullable();
      t.text('body').defaultTo('');
      t.text('source').notNullable().defaultTo('manual');
      t.text('link').defaultTo('');
      t.integer('is_read').notNullable().defaultTo(0);
      t.text('created_at').notNullable().defaultTo(knex.fn.now());
    })
    .createTable('notification_rules', (t) => {
      t.increments('id').primary();
      t.text('name').notNullable();
      t.text('event').notNullable();
      t.text('condition_field').defaultTo('');
      t.text('condition_op').defaultTo('lt');
      t.text('condition_value').defaultTo('');
      t.text('notify_role').defaultTo('');
      t.text('title_template').notNullable();
      t.text('body_template').defaultTo('');
      t.integer('is_active').notNullable().defaultTo(1);
      t.text('created_at').notNullable().defaultTo(knex.fn.now());
    })
    .createTable('vendors', (t) => {
      t.increments('id').primary();
      t.text('name').notNullable();
      t.text('contact').defaultTo('');
      t.text('phone').defaultTo('');
      t.text('address').defaultTo('');
      t.text('notes').defaultTo('');
      t.text('created_at').notNullable().defaultTo(knex.fn.now());
      t.text('updated_at').notNullable().defaultTo(knex.fn.now());
    });
}

export async function down(knex) {
  await knex.schema.dropTableIfExists('vendors').dropTableIfExists('notification_rules').dropTableIfExists('notifications').dropTableIfExists('inventory_reservations').dropTableIfExists('inventory_items');
}
