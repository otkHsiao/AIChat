import { Component, ErrorInfo, ReactNode } from 'react'
import {
  makeStyles,
  tokens,
  Button,
  Title2,
  Body1,
  Card,
  CardHeader,
} from '@fluentui/react-components'
import { ErrorCircleRegular, ArrowClockwiseRegular } from '@fluentui/react-icons'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    padding: tokens.spacingHorizontalXXL,
    backgroundColor: tokens.colorNeutralBackground2,
  },
  card: {
    maxWidth: '500px',
    width: '100%',
    textAlign: 'center',
  },
  icon: {
    fontSize: '64px',
    color: tokens.colorPaletteRedForeground1,
    marginBottom: tokens.spacingVerticalL,
  },
  title: {
    marginBottom: tokens.spacingVerticalM,
  },
  message: {
    marginBottom: tokens.spacingVerticalL,
    color: tokens.colorNeutralForeground2,
  },
  details: {
    backgroundColor: tokens.colorNeutralBackground3,
    padding: tokens.spacingHorizontalM,
    borderRadius: tokens.borderRadiusSmall,
    marginBottom: tokens.spacingVerticalL,
    textAlign: 'left',
    overflow: 'auto',
    maxHeight: '200px',
    fontSize: '12px',
    fontFamily: 'monospace',
  },
  actions: {
    display: 'flex',
    gap: tokens.spacingHorizontalM,
    justifyContent: 'center',
  },
})

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

// 使用函数组件包装类组件以使用 hooks
function ErrorFallback({
  error,
  errorInfo,
  onReset,
}: {
  error: Error | null
  errorInfo: ErrorInfo | null
  onReset: () => void
}) {
  const classes = useStyles()

  return (
    <div className={classes.container}>
      <Card className={classes.card}>
        <CardHeader
          header={
            <div style={{ width: '100%' }}>
              <ErrorCircleRegular className={classes.icon} />
              <Title2 className={classes.title} block>
                应用出现错误
              </Title2>
              <Body1 className={classes.message} block>
                抱歉，应用遇到了意外错误。请尝试刷新页面或返回首页。
              </Body1>

              {error && (
                <div className={classes.details}>
                  <strong>错误信息：</strong>
                  <br />
                  {error.message}
                  {errorInfo && (
                    <>
                      <br />
                      <br />
                      <strong>组件栈：</strong>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {errorInfo.componentStack}
                      </pre>
                    </>
                  )}
                </div>
              )}

              <div className={classes.actions}>
                <Button
                  appearance="primary"
                  icon={<ArrowClockwiseRegular />}
                  onClick={onReset}
                >
                  重试
                </Button>
                <Button
                  appearance="secondary"
                  onClick={() => (window.location.href = '/')}
                >
                  返回首页
                </Button>
              </div>
            </div>
          }
        />
      </Card>
    </div>
  )
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  }

  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.setState({ errorInfo })

    // 这里可以添加错误上报逻辑
    // 例如: sendErrorToAnalytics(error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <ErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onReset={this.handleReset}
        />
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary