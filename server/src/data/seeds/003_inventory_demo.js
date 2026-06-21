export async function seed(knex) {
  // Inventory items
  const items = [
    { name: '热咀 D20', spec: 'D20×150', total: 50, reserved: 20, unit: '个', alert_threshold: 10 },
    { name: '分流板钢板', spec: '300×400×20mm', total: 30, reserved: 8, unit: '块', alert_threshold: 5 },
    { name: '加热管', spec: '220V 500W', total: 100, reserved: 15, unit: '根', alert_threshold: 20 },
    { name: '热电偶', spec: 'K型', total: 200, reserved: 60, unit: '支', alert_threshold: 30 },
    { name: '铜电极', spec: 'E20×50', total: 15, reserved: 3, unit: '个', alert_threshold: 5 },
  ];
  await knex('inventory_items').insert(items);

  // Reserve items for orders
  const orders = await knex('orders').select('id').limit(3);
  const invItems = await knex('inventory_items').select('id');
  if (orders.length > 0 && invItems.length > 0) {
    await knex('inventory_reservations').insert([
      { item_id: invItems[0].id, order_id: orders[0].id, quantity: 10 },
      { item_id: invItems[0].id, order_id: orders[1].id, quantity: 10 },
      { item_id: invItems[1].id, order_id: orders[0].id, quantity: 5 },
      { item_id: invItems[2].id, order_id: orders[2].id, quantity: 15 },
    ]);
  }

  // Vendors
  const vendors = [
    { name: 'XX精密加工厂', contact: '王厂长', phone: '13900000001', address: '深圳龙华', notes: '主营深孔钻加工' },
    { name: 'YY热处理', contact: '陈工', phone: '13900000002', address: '东莞长安', notes: '真空热处理' },
    { name: 'ZZ表面处理', contact: '刘经理', phone: '13900000003', address: '佛山顺德', notes: '镀铬、抛光' },
  ];
  await knex('vendors').insert(vendors);

  // Auto notification rules
  const users = await knex('users').select('id', 'username');
  const adminUser = users.find(u => u.username === 'admin') || users[0];
  if (adminUser) {
    await knex('notification_rules').insert([
      { name: '库存不足预警', event: 'inventory_low', condition_field: 'total', condition_op: 'lte', condition_value: 'alert_threshold', notify_role: 'admin', title_template: '库存预警', body_template: '物料库存不足', is_active: 1 },
      { name: '订单完成通知', event: 'order_completed', condition_field: '', condition_op: '', condition_value: '', notify_role: 'admin', title_template: '订单已完成', body_template: '请安排出货', is_active: 0 },
    ]);
    // Demo notification
    const [workerUser] = users.filter(u => u.username === 'laowang');
    if (workerUser) {
      await knex('notifications').insert({ from_user_id: adminUser.id, to_user_id: workerUser.id, title: '新订单分配', body: '订单2026001已分配给你，请尽快完成深孔钻工序', source: 'manual', link: '/orders/1' });
    }
  }
}
