import { useMediaQuery } from "./useMediaQuery";

export function useIsSmallScreen() {
    return useMediaQuery("(max-width: 639px)");
}
