/** Whether any of `sets` can use variable speed (2000/2001, where speed is otherwise only 10/15/20) */
export const hasVariableSpeedSet = (sets: Array<string | null | undefined>): boolean =>
    sets.some(set => set === '2000' || set === '2001');
