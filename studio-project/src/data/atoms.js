import { atom } from "jotai";

//Atom for the chat Component
export const messagesAtom = atom([
    {
      key: 1,
      value: 'Hello! How can I help you today?',
      name: 'chatbot',
    },
]);


//Atoms for the InputArea component
export const textStatusAtom = atom('ready');

export const textAtom = atom('');
export const timerAtom = atom(null);