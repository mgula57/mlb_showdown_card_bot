from pydantic import BaseModel

from .result import Result

class Runner(BaseModel):

    id: str
    name: str
    base: int
    speed: int
    pitcher_id: str
    
    def add_bases(self, num_bases:int) -> None:
        self.base = min(self.base + num_bases, 4)

    @property
    def has_scored(self) -> bool:
        return self.base == 4
    
class Runners(BaseModel):

    runners: list[Runner] = []

    def move(self, result:Result, outs:int, hitter, pitcher, is_double_play_attempt:bool = False) -> tuple[dict,list[Runner]]:

        # DONT MOVE ANY RUNNERS IF END OF INNING
        if outs == 3:
            return {}, []
        
        new_runners = []
        is_bases_loaded = len(self.runners) == 3
        pitcher_runs_allowed_dict = {}
        runners_scored = []
        add_hitter_to_bases = not result.is_out
        if result == Result.HOMERUN:
            add_hitter_to_bases = False
            pitcher_runs_allowed_dict = {pitcher.id: 1}
            runners_scored.append(hitter.convert_to_runner(base=4, pitcher_id=pitcher.id))
        
        for runner in self.runners:
            bases_to_add = 0
            remove_runner = False
            # GB RESULT
            match result:
                case Result.GB:
                    if runner.base == 1 and is_double_play_attempt:
                        # REMOVE RUNNER AT FIRST, ADD HITTER TO FIRST BASE (FOR NOW, WILL CHANGE POST DP ROLL)
                        is_advance = False
                        bases_to_add = 0
                        remove_runner = True
                        add_hitter_to_bases = True
                    else:
                        is_advance = runner.base > 1
                        bases_to_add = int(is_advance)
                        remove_runner = not is_advance
                        add_hitter_to_bases = not is_advance
                case Result.BB:
                    match runner.base:
                        case 1:
                            bases_to_add = 1
                        case 2:
                            bases_to_add = int(1 in self.bases_occupied)
                        case 3:
                            bases_to_add = int(is_bases_loaded)
                case _:
                    bases_to_add = result.bases
                
            runner.add_bases(bases_to_add)
            if runner.has_scored:
                pitcher_runs_allowed_dict[runner.pitcher_id] = (pitcher_runs_allowed_dict.get(runner.pitcher_id, 0) + 1)
                runners_scored.append(runner)
                remove_runner = True
            
            if not remove_runner:
                new_runners.append(runner)

        self.runners = new_runners

        if add_hitter_to_bases:
            self.runners.append(hitter.convert_to_runner(base=max(result.bases,1), pitcher_id=pitcher.id))

        return pitcher_runs_allowed_dict, runners_scored
    
    @property
    def bases_occupied(self):
        return [runner.base for runner in self.runners]
    
    def count(self) -> int:
        return len(self.bases_occupied)
    
    def runner_for_base(self, base) -> Runner:
        for runner in self.runners:
            if runner.base == base:
                return runner
        return None
    
    def base_squares_str(self) -> str:
        final_str = ""
        for base in [3,2,1]:
            final_str += "■" if self.runner_for_base(base) is not None else "□"

        return final_str

    def advance_runner(self, base) -> None:
        runner = self.runner_for_base(base)
        runner.add_bases(1)

    def remove_runner(self, base) -> None:
        runner = self.runner_for_base(base)
        self.runners.remove(runner)
