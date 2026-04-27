const messages = [
  "Thanks!",
  "Thank you for the feedback!",
  "Appreciated!",
  "Noted, thanks!",
  "Good to know, thanks!",
  "Helpful, thank you!",
  "Got it, thanks!",
  "Thank you — that's useful!",
  "Thanks for the direction!",
  "Much appreciated!",
  "That helps, thank you!",
  "Thanks for letting me know!",
  "Thanks for the input!",
  "Noted — thank you!",
  "Thanks — that's clear!",
  "Thank you for the guidance!",
];

export const getFeedbackMessage = () =>
  messages[Math.floor(Math.random() * messages.length)];
