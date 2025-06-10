import { PATH_STEPS } from "./utils/navigation.utils";

export function getNavigationByIndex(index: number): [string | false, string | false] {
    let previousIndex: number | false = index - 1;
    let nextIndex: number | false = index + 1;

    if (previousIndex < 0) previousIndex = false;
    if (nextIndex >= PATH_STEPS.length) nextIndex = false;

    return [getPathByIndex(previousIndex), getPathByIndex(nextIndex)];
}

function getPathByIndex(index: number | false) {
    if(index === false) return false
    return PATH_STEPS[index];
}