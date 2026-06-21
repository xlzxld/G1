export async function seed(knex) {
  await knex('system_settings').insert([
    { key: 'company_name', value: '热流道工厂', category: 'general' },
    { key: 'order_prefix', value: '2026', category: 'order' },
    { key: 'drawing_categories', value: '分流板图,零件图,精雕图,线切割图,图纸', category: 'drawings' },
    { key: 'nozzle_models', value: 'D15,D18,D20,D25,D30', category: 'product' },
    { key: 'material_types', value: 'H13,8407,S136,SKD61,NAK80', category: 'product' },
    { key: 'product_models', value: '分流板Type-A,分流板Type-B,热咀标准型,热咀加长型', category: 'product' },
  ]);
}
