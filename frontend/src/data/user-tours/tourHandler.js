import { startTour as startNavigationTour } from "./tours/navigation-tour";
import { startTour as startPromptingTour } from "./tours/prompting-tour";

// Maps the tour ids returned by POST /tours/select (backend/src/tours/selector.py)
// to the function that starts that tour on the frontend.
const TOURS = {
  "graph-navigation": startNavigationTour,
  prompting: startPromptingTour,
};

/**
 * Starts the tour picked by the backend.
 * @param {{ tour_id: string | null }} selection response of /tours/select
 * @param {string} [question] the user's help question, shown in the chat
 * @returns {boolean} whether a tour was started
 */
export function startTour(selection, question) {
  const start = TOURS[selection?.tour_id];
  if (!start) {
    if (selection?.tour_id) {
      console.warn(`No frontend tour registered for "${selection.tour_id}"`);
    }
    return false;
  }
  start(question);
  return true;
}
