export function up(knex) {
  return knex.schema
    .createTable('process_flows', (t) => {
      t.increments('id').primary();
      t.text('name').notNullable();
      t.text('description').defaultTo('');
      t.integer('is_template').notNullable().defaultTo(0);
      t.integer('order_id').nullable();
      t.text('created_at').notNullable().defaultTo(knex.fn.now());
      t.text('updated_at').notNullable().defaultTo(knex.fn.now());
    })
    .createTable('process_steps', (t) => {
      t.increments('id').primary();
      t.integer('flow_id').notNullable().references('id').inTable('process_flows').onDelete('CASCADE');
      t.text('name').notNullable();
      t.integer('seq').notNullable().defaultTo(0);
      t.integer('required').notNullable().defaultTo(1);
      t.integer('can_parallel').notNullable().defaultTo(0);
      t.integer('depends_on_step_id').nullable();
      t.integer('outsourced').notNullable().defaultTo(0);
      t.integer('vendor_id').nullable();
      t.text('sent_date').nullable();
      t.text('return_date').nullable();
      t.float('cost').nullable();
      t.text('assignee').defaultTo('');
      t.text('completion_condition').notNullable().defaultTo('manual');
      t.text('status').notNullable().defaultTo('pending');
      t.text('started_at').nullable();
      t.text('completed_at').nullable();
      t.integer('completed_by').nullable().references('id').inTable('users').onDelete('SET NULL');
    })
    .createTable('orders', (t) => {
      t.increments('id').primary();
      t.text('order_no').notNullable().unique();
      t.text('product_name').notNullable();
      t.text('customer_name').defaultTo('');
      t.integer('priority').notNullable().defaultTo(0);
      t.text('status').notNullable().defaultTo('draft');
      t.integer('current_step_id').nullable();
      t.text('shipment_date').nullable();
      t.text('notes').defaultTo('');
      t.integer('created_by').nullable().references('id').inTable('users').onDelete('SET NULL');
      t.text('created_at').notNullable().defaultTo(knex.fn.now());
      t.text('updated_at').notNullable().defaultTo(knex.fn.now());
    });
}

export function down(knex) {
  return knex.schema.dropTableIfExists('orders').dropTableIfExists('process_steps').dropTableIfExists('process_flows');
}
