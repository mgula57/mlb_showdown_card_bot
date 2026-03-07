import webcolors

def color_name(color_tuple: tuple[int, int, int]) -> str:
    """Name of color. Will return closest value if no match."""
    
    color_tuple = color_tuple[:3]  # Ignore alpha if present
    try:
        closest_name = actual_name = webcolors.rgb_to_name(color_tuple)
    except ValueError:
        closest_name = __closest_color(color_tuple)
        actual_name = None
    final_css_color = actual_name or closest_name            
    match final_css_color:
        case 'darkslategray':
            # DARK SLATE GRAY HAS WIDE RANGE
            # APPLY GREEN TO THOSE WITH NO RED IN PROFILE
            red = color_tuple[0]
            green = color_tuple[1]
            if (green - red) > 40:
                return 'GREEN'
            else:
                return 'GRAY'
        case 'midnightblue' | 'darkblue' | 'deepskyblue' | 'navy' | 'cornflowerblue' | 'teal' | 'skyblue': return 'BLUE'
        case 'green' | 'darkkhaki' | 'forestgreen' | 'darkcyan': return 'GREEN'
        case 'crimson' | 'firebrick' | 'darkred' | 'red' | 'maroon' | 'tomato': return 'RED'
        case 'black': return 'BLACK'
        case 'lightgray' | 'silver': return 'GRAY'
        case 'orangered' | 'chocolate' | 'darkorange' | 'coral': return 'ORANGE'
        case 'gold' | 'goldenrod' | 'lemonchiffon': return 'YELLOW'
        case 'darkslateblue': return 'PURPLE'
        case 'brown' | 'saddlebrown' | 'sandybrown' | 'wheat' | 'peru': return 'BROWN'
        case _: return None    

def __closest_color(requested_color: tuple[int,int,int]) -> str:
    """Closest matched name of color given rgbs"""
    min_colors = {}
    for name in webcolors.names("css3"):
        r_c, g_c, b_c = webcolors.name_to_rgb(name)
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_colors[(rd + gd + bd)] = name
    
    return min_colors[min(min_colors.keys())]