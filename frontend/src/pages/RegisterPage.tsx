import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Card,
  CardHeader,
  CardPreview,
  Input,
  Button,
  Field,
  Spinner,
  MessageBar,
  MessageBarBody,
  Title1,
  Body1,
} from '@fluentui/react-components'
import {
  PersonRegular,
  LockClosedRegular,
  MailRegular,
} from '@fluentui/react-icons'

import { useAppDispatch } from '../hooks/useAppDispatch'
import { setCredentials } from '../features/auth/authSlice'
import type { RegisterData, AuthResponse } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export default function RegisterPage() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()

  const [formData, setFormData] = useState<RegisterData>({
    email: '',
    username: '',
    password: '',
  })
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validate passwords match
    if (formData.password !== confirmPassword) {
      setError('两次输入的密码不一致')
      return
    }

    // Validate password strength
    if (formData.password.length < 8) {
      setError('密码长度至少为8位')
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || '注册失败')
      }

      const authData: AuthResponse = data.data || data
      dispatch(setCredentials({
        user: authData.user,
        accessToken: authData.accessToken,
        refreshToken: authData.refreshToken,
      }))

      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : '注册失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f5f5',
        padding: '20px',
      }}
    >
      <Card style={{ width: '100%', maxWidth: '400px' }}>
        <CardHeader
          header={
            <div style={{ textAlign: 'center', width: '100%' }}>
              <Title1>AI Chat</Title1>
              <Body1>创建新账户</Body1>
            </div>
          }
        />
        <CardPreview>
          <form onSubmit={handleSubmit} style={{ padding: '20px' }}>
            {error && (
              <MessageBar intent="error" style={{ marginBottom: '16px' }}>
                <MessageBarBody>{error}</MessageBarBody>
              </MessageBar>
            )}

            <Field label="邮箱" required style={{ marginBottom: '16px' }}>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                contentBefore={<MailRegular />}
                placeholder="your@email.com"
                disabled={isLoading}
              />
            </Field>

            <Field label="用户名" required style={{ marginBottom: '16px' }}>
              <Input
                type="text"
                value={formData.username}
                onChange={(e) =>
                  setFormData({ ...formData, username: e.target.value })
                }
                contentBefore={<PersonRegular />}
                placeholder="用户名"
                disabled={isLoading}
              />
            </Field>

            <Field label="密码" required style={{ marginBottom: '16px' }}>
              <Input
                type="password"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                contentBefore={<LockClosedRegular />}
                placeholder="至少8位字符"
                disabled={isLoading}
              />
            </Field>

            <Field label="确认密码" required style={{ marginBottom: '24px' }}>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                contentBefore={<LockClosedRegular />}
                placeholder="再次输入密码"
                disabled={isLoading}
              />
            </Field>

            <Button
              type="submit"
              appearance="primary"
              style={{ width: '100%', marginBottom: '16px' }}
              disabled={isLoading}
            >
              {isLoading ? <Spinner size="tiny" /> : '注册'}
            </Button>

            <div style={{ textAlign: 'center' }}>
              <Body1>
                已有账户？{' '}
                <Link to="/login" style={{ color: '#0078d4' }}>
                  登录
                </Link>
              </Body1>
            </div>
          </form>
        </CardPreview>
      </Card>
    </div>
  )
}