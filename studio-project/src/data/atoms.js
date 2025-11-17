import { atom, selectAtom } from "jotai";

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

//Atom for the knowledge graph component
export const graphDataAtom = atom({
    nodes: [],
    edges: [],
    draggingNodeId:null,
    selectedNodeId:null,

});

export const nodesAtom = selectAtom(graphDataAtom, (u) => u?.nodes ?? []);

export const edgesAtom = selectAtom(graphDataAtom, (u) => u?.edges ?? []);

export const selectedNodeAtom = selectAtom(graphDataAtom, (u) => u?.selectedNodeAtom ?? null);

export const draggingNodeIdAtom = selectAtom(graphDataAtom, (u) => u?.draggingNodeId ?? null);
