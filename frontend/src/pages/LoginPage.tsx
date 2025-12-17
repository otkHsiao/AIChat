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
import { PersonRegular, LockClosedRegular } from '@fluentui/react-icons'

import { useAppDispatch } from '../hooks/useAppDispatch'
import { setCredentials } from '../features/auth/authSlice'
import type { LoginCredentials, AuthResponse } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export default function LoginPage() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()

  const [credentials, setCredentialsState] = useState<LoginCredentials>({
    email: '',
    password: '',
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || '登录失败')
      }

      const authData: AuthResponse = data.data || data
      dispatch(setCredentials({
        user: authData.user,
        accessToken: authData.accessToken,
        refreshToken: authData.refreshToken,
      }))

      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败，请重试')
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
              <Body1>登录您的账户</Body1>
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
                value={credentials.email}
                onChange={(e) =>
                  setCredentialsState({ ...credentials, email: e.target.value })
                }
                contentBefore={<PersonRegular />}
                placeholder="your@email.com"
                disabled={isLoading}
              />
            </Field>

            <Field label="密码" required style={{ marginBottom: '24px' }}>
              <Input
                type="password"
                value={credentials.password}
                onChange={(e) =>
                  setCredentialsState({ ...credentials, password: e.target.value })
                }
                contentBefore={<LockClosedRegular />}
                placeholder="输入密码"
                disabled={isLoading}
              />
            </Field>

            <Button
              type="submit"
              appearance="primary"
              style={{ width: '100%', marginBottom: '16px' }}
              disabled={isLoading}
            >
              {isLoading ? <Spinner size="tiny" /> : '登录'}
            </Button>

            <div style={{ textAlign: 'center' }}>
              <Body1>
                还没有账户？{' '}
                <Link to="/register" style={{ color: '#0078d4' }}>
                  注册
                </Link>
              </Body1>
            </div>
          </form>
        </CardPreview>
      </Card>
    </div>
  )
}