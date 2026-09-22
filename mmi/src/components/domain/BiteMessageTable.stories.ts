import type { Meta, StoryObj } from '@storybook/vue3-vite'
import BiteMessageTable from './BiteMessageTable.vue'
import type { BiteEventMessage } from '@/types/mmi'

const now = Date.now()
const iso = (msAgo: number) => new Date(now - msAgo).toISOString()

const mockBiteHistory: BiteEventMessage[] = [
  { type: 'bite_event', signal_id: 'tx.interlock_ok_status', transition: 'fault', detail: 'interlock de transmisor abierto', at_wall: iso(300_000) },
  { type: 'bite_event', signal_id: 'ant.servo_ok_status', transition: 'cleared', detail: 'servo de antena restablecido', at_wall: iso(600_000) },
  { type: 'bite_event', signal_id: 'ant.servo_ok_status', transition: 'fault', detail: 'servo sin respuesta', at_wall: iso(1_200_000) },
  { type: 'bite_event', signal_id: 'sys.environment_ok_status', transition: 'cleared', detail: 'temperatura normalizada', at_wall: iso(2_400_000) },
  { type: 'bite_event', signal_id: 'sys.environment_ok_status', transition: 'fault', detail: 'sobretemperatura gabinete', at_wall: iso(3_600_000) },
]

const meta: Meta<typeof BiteMessageTable> = {
  title: 'Domain/BiteMessageTable (B9)',
  component: BiteMessageTable,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    rows: mockBiteHistory,
  },
}

export const Empty: Story = {
  args: {
    rows: [],
  },
}
