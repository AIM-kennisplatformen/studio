import { atom } from "jotai";

//Atom for the chat Component
export const messagesAtom = atom([
    {
      key: 1,
      value: '## Hello! \n **How can I help you today?**',
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
