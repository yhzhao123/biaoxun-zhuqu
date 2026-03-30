import React from 'react';
import { Layout, Menu, Badge, Avatar, Dropdown, Space } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  BarChartOutlined,
  LineChartOutlined,
  AppstoreOutlined,
  BellOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAppStore } from '@/stores/appStore';

const { Header, Sider, Content } = Layout;

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const unreadCount = useAppStore((state) => state.unreadCount());
  
  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: '仪表板' },
    { key: '/tenders', icon: <FileTextOutlined />, label: '招标列表' },
    { key: '/opportunity', icon: <BarChartOutlined />, label: '商机分析' },
    { key: '/trends', icon: <LineChartOutlined />, label: '趋势分析' },
    { key: '/classification', icon: <AppstoreOutlined />, label: '数据分类' },
    { key: '/realtime', icon: <BellOutlined />, label: '实时推送', badge: unreadCount() },
    { key: '/settings', icon: <SettingOutlined />, label: '设置' },
  ];
  
  const userMenuItems = [
    { key: 'profile', label: '个人资料' },
    { key: 'settings', label: '账号设置' },
    { key: 'logout', label: '退出登录' },
  ];
  
  const handleMenuClick = (key: string) => {
    if (key === 'logout') {
      localStorage.removeItem('token');
      navigate('/login');
    } else if (key === 'profile') {
      navigate('/profile');
    } else if (key === 'settings') {
      navigate('/settings');
    }
  };
  
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        theme="light"
        width={200}
        style={{
          boxShadow: '2px 0 8px rgba(0,0,0,0.06)',
          zIndex: 10,
        }}
      >
        <div className="h-16 flex items-center justify-center border-b border-gray-200">
          <h1 className="text-xl font-bold text-primary">标讯 · 筑渠</h1>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems.map(item => ({
            key: item.key,
            icon: item.icon,
            label: item.badge ? (
              <Space>
                {item.label}
                <Badge count={item.badge} size="small" />
              </Space>
            ) : item.label,
          }))}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0 }}
        />
      </Sider>
      
      <Layout>
        <Header className="bg-white px-6 flex items-center justify-between shadow-sm">
          <h2 className="text-lg font-medium">
            {menuItems.find(item => item.key === location.pathname)?.label || '标讯筑渠'}
          </h2>
          
          <Space size={24}>
            <Badge count={unreadCount()} size="small">
              <BellOutlined className="text-xl cursor-pointer" onClick={() => navigate('/realtime')} />
            </Badge>
            
            <Dropdown
              menu={{ items: userMenuItems, onClick: ({ key }) => handleMenuClick(key) }}
              placement="bottomRight"
            >
              <Space className="cursor-pointer">
                <Avatar icon={<UserOutlined />} />
                <span>管理员</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        
        <Content className="p-6 bg-gray-50 overflow-auto">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
