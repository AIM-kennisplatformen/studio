import { atom } from 'jotai'
import { customAlphabet } from 'nanoid'

// Generate chat ID: 20 chars grouped in 5s with hyphens (xxxxx-xxxxx-xxxxx-xxxxx)
const alphabet =
  '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
const nanoid = customAlphabet(alphabet, 20)

function generateChatId() {
  const id = nanoid()
  return `${id.slice(0, 5)}-${id.slice(5, 10)}-${id.slice(10, 15)}-${id.slice(15, 20)}`
}

// Atom for the chat ID - initialized once on app load
export const chatIdAtom = atom(generateChatId())

//Atom for the chat Component
export const messagesAtom = atom([
  {
    key: 1,
    value: `Welcome to the knowledge platform for Energy Poverty Intervention Strategies!\n
Discover expert insights on tackling energy poverty, drawn from scientific research, policy reports, and real-world best practices across Europe.  

What would you like to explore today?`,
    name: 'chatbot',
  },
])

// Atom for the last completed chatbot message key (show actions on this message)
export const lastDoneMessageKeyAtom = atom(null)

//Atoms for the InputArea component
export const textStatusAtom = atom('ready')
export const textAtom = atom('')
export const timerAtom = atom(null)

//Atoms for the graph component
export const nodesAtom = atom([])
export const edgesAtom = atom([])
export const selectedNodeAtom = atom(null)
export const centerNodeAtom = atom(1)
export const dataAtom = atom(null)
export const layoutNodesAtom = atom([])
