import React, { useState } from 'react';
import { Card, Form, Input, Button, Switch, Select, Slider, message, Tabs } from 'antd';
import { SaveOutlined, BellOutlined, SettingOutlined, UserOutlined } from '@ant-design/icons';

const SettingsPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSave = async (values: any) => {
    setLoading(true);
    setTimeout(() => {
      message.success('设置已保存');
      setLoading(false);
    }, 1000);
  };

  return (
    <div>
      <Tabs
        items={[
          {
            key: 'general',
            label: (<span><SettingOutlined /> 通用设置</span>),
            children: (
              <Card>
                <Form form={form} layout="vertical" onFinish={handleSave} initialValues={{ refreshInterval: 5, pageSize: 20 }}>
                  <Form.Item label="自动刷新间隔（分钟）" name="refreshInterval">
                    <Slider min={1} max={60} marks={{ 5: '5分钟', 15: '15分钟', 30: '30分钟', 60: '60分钟' }} />
                  </Form.Item>
                  <Form.Item label="每页显示数量" name="pageSize">
                    <Select options={[{ value: 10, label: '10条' }, { value: 20, label: '20条' }, { value: 50, label: '50条' }, { value: 100, label: '100条' }]} />
                  </Form.Item>
                  <Form.Item label="商机评分阈值" name="threshold">
                    <Slider min={50} max={100} marks={{ 50: '50分', 70: '70分', 80: '80分', 90: '90分' }} />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>保存设置</Button>
                  </Form.Item>
                </Form>
              </Card>
            ),
          },
          {
            key: 'notifications',
            label: (<span><BellOutlined /> 通知设置</span>),
            children: (
              <Card>
                <Form layout="vertical">
                  <Form.Item label="启用推送通知">
                    <Switch defaultChecked />
                  </Form.Item>
                  <Form.Item label="新招标通知">
                    <Switch defaultChecked />
                  </Form.Item>
                  <Form.Item label="高价值商机提醒">
                    <Switch defaultChecked />
                  </Form.Item>
                  <Form.Item label="截止提醒">
                    <Switch defaultChecked />
                  </Form.Item>
                </Form>
              </Card>
            ),
          },
          {
            key: 'api',
            label: (<span><UserOutlined /> API配置</span>),
            children: (
              <Card>
                <Form layout="vertical">
                  <Form.Item label="API地址" name="apiUrl">
                    <Input defaultValue="http://localhost:8000" />
                  </Form.Item>
                  <Form.Item label="WebSocket地址" name="wsUrl">
                    <Input defaultValue="ws://localhost:8000/ws" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" icon={<SaveOutlined />}>保存配置</Button>
                  </Form.Item>
                </Form>
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
};

export default SettingsPage;
