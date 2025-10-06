import GamesForDate from "../games/GamesForDate";

function HomePage() {

    return (
        <div className="px-4">
            <span className="text-xl font-black w-full">Games</span>
            <GamesForDate date={new Date().toISOString().split('T')[0]} />
        </div>
    );
}

export default HomePage;
