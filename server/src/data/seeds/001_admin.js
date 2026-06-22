import bcrypt from 'bcryptjs';

export async function seed(knex) {
  await knex('page_permissions').del();
  await knex('users').del();

  const hash = await bcrypt.hash('admin123', 10);
  const [adminId] = await knex('users').insert({
    username: 'admin',
    display_name: '管理员',
    role_label: '管理员',
    password_hash: hash,
    is_admin: 1,
  });

  const pages = ['dashboard','customers','orders','process_flow','drawings','inventory','users','notifications','settings','outsourcing'];
  const perms = pages.map((key) => ({
    user_id: adminId,
    page_key: key,
    can_view: 1,
    can_edit: 1,
  }));
  await knex('page_permissions').insert(perms);
}
