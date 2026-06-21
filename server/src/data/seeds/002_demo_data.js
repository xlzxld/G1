import bcrypt from 'bcryptjs';

export async function seed(knex) {
  const now = new Date().toISOString();

  const hash = await bcrypt.hash('123456', 10);
  const [workerId] = await knex('users').insert({ username: 'laowang', display_name: '老王', role_label: '车间工人', password_hash: hash, is_admin: 0 });
  const [designerId] = await knex('users').insert({ username: 'xiaoli', display_name: '小李', role_label: '设计师', password_hash: hash, is_admin: 0 });

  const pages = ['dashboard','customers','orders','process_flow','drawings','inventory','users','notifications','settings','outsourcing'];
  for (const uid of [workerId, designerId]) {
    const perms = pages.map((k) => ({ user_id: uid, page_key: k, can_view: 1, can_edit: k === 'users' || k === 'notifications' ? 0 : 1 }));
    await knex('page_permissions').insert(perms);
  }

  // Create customers
  const [cust1] = await knex('customers').insert({ name: 'XX精密模具', contact: '张经理', phone: '13800000001', address: '深圳龙华', wechat: 'zhang_mgr', email: 'zhang@xx.com' });
  const [cust2] = await knex('customers').insert({ name: 'YY注塑科技', contact: '李工', phone: '13800000002', address: '东莞长安' });

  // Create process template
  const [flowId] = await knex('process_flows').insert({ name: '标准热流道流程', description: '从接单到出货的完整流程', is_template: 1, created_at: now, updated_at: now });
  const steps = [
    { flow_id: flowId, name: '接单', seq: 0, required: 1, can_parallel: 0, assignee: 'admin', status: 'pending' },
    { flow_id: flowId, name: '设计', seq: 1, required: 1, can_parallel: 0, assignee: 'xiaoli', status: 'pending' },
    { flow_id: flowId, name: '下料', seq: 2, required: 1, can_parallel: 1, assignee: 'laowang', status: 'pending' },
    { flow_id: flowId, name: '深孔钻', seq: 3, required: 1, can_parallel: 0, assignee: 'laowang', status: 'pending' },
    { flow_id: flowId, name: '精雕', seq: 4, required: 1, can_parallel: 0, assignee: 'laowang', status: 'pending' },
    { flow_id: flowId, name: '抛光', seq: 5, required: 1, can_parallel: 0, assignee: 'laowang', status: 'pending' },
    { flow_id: flowId, name: '质检', seq: 6, required: 0, can_parallel: 0, assignee: 'admin', status: 'pending' },
    { flow_id: flowId, name: '出货', seq: 7, required: 1, can_parallel: 0, assignee: 'admin', status: 'pending' },
  ];
  await knex('process_steps').insert(steps);

  // Create demo orders
  const orders = [
    { order_no: '2026001', product_name: '分流板 Type-A', customer_id: cust1, priority: 2, shipment_date: '2026-07-15', created_by: 1 },
    { order_no: '2026002', product_name: '热咀 D20', customer_id: cust1, priority: 1, shipment_date: '2026-06-30', created_by: 1 },
    { order_no: '2026003', product_name: '分流板 Type-B', customer_id: cust2, priority: 0, shipment_date: '2026-08-05', created_by: 1 },
  ];

  for (const o of orders) {
    const [orderId] = await knex('orders').insert({ ...o, status: 'draft', created_at: now, updated_at: now });
    const [orderFlowId] = await knex('process_flows').insert({ name: '标准热流道流程', is_template: 0, order_id: orderId, created_at: now, updated_at: now });
    const templateSteps = await knex('process_steps').where({ flow_id: flowId }).orderBy('seq', 'asc');
    const idMap = {};
    for (const s of templateSteps) {
      const [newId] = await knex('process_steps').insert({
        flow_id: orderFlowId, name: s.name, seq: s.seq, required: s.required,
        can_parallel: s.can_parallel || 0, assignee: s.assignee, status: 'pending',
      });
      idMap[s.id] = newId;
    }
    for (const s of templateSteps) {
      if (s.depends_on_step_id && idMap[s.depends_on_step_id]) {
        await knex('process_steps').where({ id: idMap[s.id] }).update({ depends_on_step_id: idMap[s.depends_on_step_id] });
      }
    }
    const firstStep = await knex('process_steps').where({ flow_id: orderFlowId }).orderBy('seq', 'asc').first();
    if (firstStep) {
      await knex('orders').where({ id: orderId }).update({ current_step_id: firstStep.id, status: firstStep.name + '进行中' });
    }
  }
}
