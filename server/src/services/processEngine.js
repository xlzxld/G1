import { db } from '../app.js';

export async function advanceStep(stepId, userId) {
  const step = await db('process_steps').where({ id: stepId }).first();
  if (!step) throw new Error('Step not found');
  if (step.status !== 'pending' && step.status !== 'in_progress') throw new Error('Step not actionable');

  const now = new Date().toISOString();
  const updates = { status: 'completed', completed_at: now, completed_by: userId, started_at: step.started_at || now };
  await db('process_steps').where({ id: stepId }).update(updates);

  const flow = await db('process_flows').where({ id: step.flow_id }).first();
  if (!flow) throw new Error('Flow not found');

  if (flow.is_template) {
    return { step: { id: stepId, ...updates }, flow: { id: flow.id }, is_template: true };
  }

  const nextSteps = await getNextSteps(flow.id);
  const prevSteps = await db('process_steps').where({ flow_id: flow.id }).whereIn('status', ['pending']);
  const allDone = prevSteps.length === 0;

  let orderStatus = step.name + '已完成';
  if (nextSteps.length > 0) {
    orderStatus = nextSteps[0].name + '进行中';
  }
  if (allDone) {
    orderStatus = 'completed';
  }

  const orderUpdates = { status: orderStatus, updated_at: now };
  if (nextSteps.length > 0) {
    orderUpdates.current_step_id = nextSteps[0].id;
  }
  await db('orders').where({ id: flow.order_id }).update(orderUpdates);

  return { step: { id: stepId, ...updates }, nextSteps, orderStatus, is_template: false };
}

export async function rollbackStep(stepId, userId) {
  const step = await db('process_steps').where({ id: stepId }).first();
  if (!step) throw new Error('Step not found');
  if (step.status !== 'completed' && step.status !== 'skipped') throw new Error('Can only rollback completed or skipped steps');

  const now = new Date().toISOString();
  await db('process_steps').where({ id: stepId }).update({
    status: 'pending', completed_at: null, completed_by: null, started_at: null,
  });

  const flow = await db('process_flows').where({ id: step.flow_id }).first();
  // When rolling back, find the correct previous step.
  // If the rolled-back step is parallel, go before the parallel group starts.
  let prevSeq = step.seq - 1;
  if (step.can_parallel) {
    const allSteps = await db('process_steps').where({ flow_id: flow.id }).orderBy('seq', 'asc');
    while (prevSeq >= 0 && allSteps[prevSeq]?.can_parallel) prevSeq--;
  }
  const prevStep = await db('process_steps')
    .where({ flow_id: flow.id }).where('seq', prevSeq)
    .first();

  const statusName = prevStep ? prevStep.name + '进行中' : 'draft';
  await db('orders').where({ id: flow.order_id }).update({
    status: statusName,
    current_step_id: prevStep ? prevStep.id : null,
    updated_at: now,
  });
  return { rolledBack: stepId, orderStatus: statusName };
}

export async function skipStep(stepId, userId) {
  const step = await db('process_steps').where({ id: stepId }).first();
  if (!step) throw new Error('Step not found');
  if (step.required) throw new Error('Cannot skip required step');
  if (step.status !== 'pending') throw new Error('Step not skippable');

  const now = new Date().toISOString();
  await db('process_steps').where({ id: stepId }).update({
    status: 'skipped', completed_at: now, completed_by: userId,
  });

  const flow = await db('process_flows').where({ id: step.flow_id }).first();
  const nextSteps = await getNextSteps(flow.id);
  let orderStatus = step.name + '已跳过';
  if (nextSteps.length > 0) {
    orderStatus = nextSteps[0].name + '进行中';
    await db('orders').where({ id: flow.order_id }).update({ status: orderStatus, current_step_id: nextSteps[0].id, updated_at: now });
  }
  return { skipped: stepId, nextSteps, orderStatus };
}

export async function getNextSteps(flowId) {
  const all = await db('process_steps').where({ flow_id: flowId }).orderBy('seq', 'asc');
  const completedIds = all.filter((s) => s.status === 'completed' || s.status === 'skipped').map((s) => s.id);
  const pending = all.filter((s) => s.status === 'pending');

  const ready = pending.filter((s) => {
    if (!s.depends_on_step_id) return true;
    return completedIds.includes(s.depends_on_step_id);
  });

  const inProgress = all.filter((s) => s.status === 'in_progress');
  const canParallel = ready.filter((s) => {
    if (!s.can_parallel) return inProgress.length === 0;
    return true;
  });

  if (canParallel.length > 0) return canParallel;
  if (ready.length > 0) return [ready[0]];
  if (inProgress.length > 0) return inProgress;
  return [];
}

export async function copyFlowToOrder(templateFlowId, orderId) {
  const template = await db('process_flows').where({ id: templateFlowId, is_template: 1 }).first();
  if (!template) throw new Error('Template not found');

  const [newFlowId] = await db('process_flows').insert({
    name: template.name, description: template.description,
    is_template: 0, order_id: orderId,
  });

  const templateSteps = await db('process_steps').where({ flow_id: templateFlowId }).orderBy('seq', 'asc');
  if (templateSteps.length === 0) return newFlowId;

  // Copy steps, mapping depends_on_step_id to new IDs later
  const stepMap = {};
  for (const s of templateSteps) {
    const [newId] = await db('process_steps').insert({
      flow_id: newFlowId, name: s.name, seq: s.seq,
      required: s.required, can_parallel: s.can_parallel,
      completion_condition: s.completion_condition, assignee: s.assignee,
      outsourced: s.outsourced, vendor_id: s.vendor_id,
      status: 'pending',
    });
    stepMap[s.id] = newId;
  }

  // Fix depends_on
  for (const [oldId, newId] of Object.entries(stepMap)) {
    const oldStep = templateSteps.find((s) => s.id === Number(oldId));
    if (oldStep?.depends_on_step_id && stepMap[oldStep.depends_on_step_id]) {
      await db('process_steps').where({ id: newId }).update({
        depends_on_step_id: stepMap[oldStep.depends_on_step_id],
      });
    }
  }

  // Set first step as current
  if (templateSteps.length > 0) {
    const firstStepId = stepMap[templateSteps[0].id];
    const now = new Date().toISOString();
    await db('orders').where({ id: orderId }).update({
      status: templateSteps[0].name + '进行中',
      current_step_id: firstStepId,
      updated_at: now,
    });
  }

  return newFlowId;
}
