import { atom } from "jotai";

//Atom for the chat Component
export const messagesAtom = atom([
  {
    key: 1,
    value: `Welcome to the knowledge platform for Energy Poverty Intervention Strategies!\n
Discover expert insights on tackling energy poverty, drawn from scientific research, policy reports, and real-world best practices across Europe.  

What would you like to explore today?`,
    name: 'chatbot',
  },
]);




//Atoms for the InputArea component
export const textStatusAtom = atom('ready');
export const textAtom = atom('');
export const timerAtom = atom(null);

//Atoms for the graph component
export const nodesAtom = atom([]);
export const edgesAtom = atom([]);
export const selectedNodeAtom = atom(null);
export const draggingNodeIdAtom = atom(null);
