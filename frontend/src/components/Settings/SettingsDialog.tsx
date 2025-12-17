import { useState } from 'react'
import {
  Dialog,
  DialogTrigger,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
  Button,
  Select,
  Label,
  makeStyles,
  tokens,
} from '@fluentui/react-components'
import { Settings24Regular, Dismiss24Regular } from '@fluentui/react-icons'
import { useAppSelector, useAppDispatch } from '../../store'
import { setTheme } from '../../features/ui/uiSlice'

const useStyles = makeStyles({
  content: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalL,
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalXS,
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
})

interface SettingsDialogProps {
  trigger?: React.ReactElement
}

export default function SettingsDialog({ trigger }: SettingsDialogProps) {
  const classes = useStyles()
  const dispatch = useAppDispatch()
  const theme = useAppSelector((state) => state.ui.theme)
  const [open, setOpen] = useState(false)

  const handleThemeChange = (value: string) => {
    dispatch(setTheme(value as 'light' | 'dark'))
  }

  return (
    <Dialog open={open} onOpenChange={(_, data) => setOpen(data.open)}>
      <DialogTrigger disableButtonEnhancement>
        {trigger || (
          <Button appearance="subtle" icon={<Settings24Regular />}>
            设置
          </Button>
        )}
      </DialogTrigger>

      <DialogSurface>
        <DialogBody>
          <div className={classes.header}>
            <DialogTitle>设置</DialogTitle>
            <Button
              appearance="subtle"
              icon={<Dismiss24Regular />}
              onClick={() => setOpen(false)}
            />
          </div>

          <DialogContent className={classes.content}>
            <div className={classes.field}>
              <Label htmlFor="theme-select">主题</Label>
              <Select
                id="theme-select"
                value={theme}
                onChange={(_, data) => handleThemeChange(data.value)}
              >
                <option value="light">浅色</option>
                <option value="dark">深色</option>
              </Select>
            </div>

            <div className={classes.field}>
              <Label htmlFor="model-select">默认模型</Label>
              <Select id="model-select" defaultValue="gpt-4o">
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4">GPT-4</option>
              </Select>
            </div>
          </DialogContent>

          <DialogActions>
            <Button appearance="secondary" onClick={() => setOpen(false)}>
              关闭
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  )
}