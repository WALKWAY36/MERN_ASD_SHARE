function cors(req, res, next) {
    res.header("Access-Control-Allow-Origin", "http://c1r011v08.amm.vsu.ru"); // Указываем конкретный источник
    res.header("Access-Control-Allow-Methods", "GET, PUT, PATCH, POST, DELETE");
    res.header("Access-Control-Allow-Headers", "Content-Type, Authorization");
    res.header("Access-Control-Allow-Credentials", "true"); // Разрешаем использование credentials (например, куки)

    // Обработка preflight запросов
    if (req.method === 'OPTIONS') {
        return res.sendStatus(204);
    }


    next();
}

export default cors
