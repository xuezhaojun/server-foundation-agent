// @ts-nocheck
/** @jsxImportSource @opentui/solid */
import type { TuiPlugin, TuiPluginModule, TuiSlotPlugin, TuiThemeCurrent } from "@opencode-ai/plugin/tui"
import { useTerminalDimensions } from "@opentui/solid"
import { createMemo, createSignal } from "solid-js"

const id = "sfa"

// Small: compact for narrow terminals
const logoSmall = [
  "┌─────────────────────┐",
  "│  Server Foundation  │",
  "└─────────────────────┘",
]

// Medium: block-style ASCII art
const logoMedium = [
  "╭──────────────────────────────────────────────────╮",
  "│                                                  │",
  "│   ███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗",
  "│   ██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗",
  "│   ███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝",
  "│   ╚════██║██╔══╝  ██╔══██╗╚██╗ ██╔╝██╔══╝  ██╔══██╗",
  "│   ███████║███████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║",
  "│   ╚══════╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝",
  "│                                                  │",
  "│   ███████╗ ██████╗ ██╗   ██╗███╗   ██╗██████╗    │",
  "│   ██╔════╝██╔═══██╗██║   ██║████╗  ██║██╔══██╗   │",
  "│   █████╗  ██║   ██║██║   ██║██╔██╗ ██║██║  ██║   │",
  "│   ██╔══╝  ██║   ██║██║   ██║██║╚██╗██║██║  ██║   │",
  "│   ██║     ╚██████╔╝╚██████╔╝██║ ╚████║██████╔╝   │",
  "│   ╚═╝      ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═════╝    │",
  "│                                                  │",
  "╰──────────────────────────────────────────────────╯",
]

// Large: clean block style
const logoLarge = [
  "",
  "  ███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗ ",
  "  ██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗",
  "  ███████╗█████╗  ██████╔╝╚██╗ ██╔╝█████╗  ██████╔╝",
  "  ╚════██║██╔══╝  ██╔══██╗ ╚████╔╝ ██╔══╝  ██╔══██╗",
  "  ███████║███████╗██║  ██║  ╚██╔╝  ███████╗██║  ██║",
  "  ╚══════╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝",
  "",
  "  ███████╗ █████╗ ██╗   ██╗███╗   ██╗██████╗  █████╗ ████████╗██╗ █████╗ ███╗   ██╗",
  "  ██╔════╝██╔══██╗██║   ██║████╗  ██║██╔══██╗██╔══██╗╚══██╔══╝██║██╔══██╗████╗  ██║",
  "  █████╗  ██║  ██║██║   ██║██╔██╗ ██║██║  ██║███████║  ██║   ██║██║  ██║██╔██╗ ██║",
  "  ██╔══╝  ██║  ██║██║   ██║██║╚██╗██║██║  ██║██╔══██║  ██║   ██║██║  ██║██║╚██╗██║",
  "  ██║     ╚█████╔╝╚██████╔╝██║ ╚████║██████╔╝██║  ██║  ██║   ██║╚█████╔╝██║ ╚████║",
  "  ╚═╝      ╚════╝  ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝  ╚═╝   ╚═╝ ╚════╝ ╚═╝  ╚═══╝",
  "",
]

const width = (list: string[]) => Math.max(...list.map((l) => l.length))

const logoSmallW = width(logoSmall)
const logoMediumW = width(logoMedium)
const logoLargeW = width(logoLarge)

// Fixed color that works on both light and dark backgrounds
const LOGO_COLOR = "#06b6d4" // teal/cyan

const Home = (props: { theme: TuiThemeCurrent }) => {
  const dim = useTerminalDimensions()
  const [gap, setGap] = createSignal({ width: 0, height: 0 })

  const logo = createMemo(() => {
    const term = dim()
    const chrome = gap()
    const h = Math.max(0, term.height - chrome.height)
    const w = Math.max(0, term.width - chrome.width)
    if (h >= logoLarge.length && w >= logoLargeW) return logoLarge
    if (h >= logoMedium.length && w >= logoMediumW) return logoMedium
    return logoSmall
  })

  return (
    <box
      onSizeChange={function () {
        const term = dim()
        const own = { width: this.width, height: this.height }
        const next = {
          width: Math.max(0, term.width - own.width),
          height: Math.max(0, term.height - own.height),
        }
        setGap((prev) => {
          const w = prev.width > 0 ? Math.min(prev.width, next.width) : next.width
          const h = prev.height > 0 ? Math.min(prev.height, next.height) : next.height
          if (prev.width === w && prev.height === h) return prev
          return { width: w, height: h }
        })
      }}
      flexDirection="column"
      alignItems="center"
    >
      {(() => {
        const lines = logo()
        const isSmall = lines === logoSmall
        return lines.map((line, i) => (
          <text fg={isSmall ? LOGO_COLOR : (i === 0 || i === lines.length - 1) ? props.theme.textMuted : LOGO_COLOR}>
            {line}
          </text>
        ))
      })()}
    </box>
  )
}

const tui: TuiPlugin = async (api) => {
  const slots: TuiSlotPlugin[] = [
    {
      slots: {
        home_logo(ctx) {
          return <Home theme={ctx.theme.current} />
        },
      },
    },
  ]

  for (const item of slots) {
    api.slots.register(item)
  }
}

const plugin: TuiPluginModule & { id: string } = {
  id,
  tui,
}

export default plugin
