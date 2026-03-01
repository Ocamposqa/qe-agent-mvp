# Quantum QE Agent - Guía de Prompt Engineering

Para que el Agente QE ejecute misiones de manera limpia, sin consumir tus cuotas de tokens de OpenAI en bucles infinitos y sin confundir su estado interno en LangGraph, los 'Prompts' o 'Instrucciones' deben tener límites arquitectónicos claros.

## ❌ El Prompt Incorrecto (Anti-Patrón)
> "Ve a https://sqasa.co/ navega por todos los menús principales, verifica que funcionan correctamente también verifica que el formulario de contacto funciona correctamente"

**¿Por qué falla y congela el servidor?**
- **"Todos los menús"**: Esto obliga al Agente a iniciar un bucle forzado (*Open-ended loop*). En cada intento, el Agente lee el DOM (aproximadamente 20,000 tokens de contexto) buscando nuevos enlaces. Esto choca casi de inmediato con el límite **TPM (Tokens per Minute) de OpenAI**, arrojando el Error 429.
- **Doble Tarea Confusa**: Obligas al agente a mantener el contexto mental de "menús" mientras intenta llenar un "formulario". Una mente dispersa lleva a alucinaciones.
- **Sin línea de meta**: No hay una condición clara de salida, por lo que el agente seguirá iterando hasta colapsar.

---

## ✅ El Prompt Perfecto (Optimizado)
Los prompts óptimos para un Agente ReAct (Reason+Act) siguen el marco de trabajo **A-C-E**:
1. **Acción** (Qué pasos físicos hacer).
2. **Contexto** (En qué URL específica).
3. **Expectativa de Salida** (Qué significa que la prueba pasó o falló).

### Ejemplo 1: Prueba Funcional Directa
> "Navega directamente a https://sqasa.co/contacto. Llena el campo de email con 'test@qa.com' y presiona el botón 'Enviar'. Verifica leyendo el DOM que aparezca un banner de agradecimiento. Si aparece, reporta éxito y detente. Si no, reporta fallo y detente."

**Por qué funciona:**
- Está rígidamente dirigido a un solo flujo (Formulario).
- Condición de salida estricta ("... y detente").
- Consumo mínimo de Tokens por iteración.

### Ejemplo 2: Navegación Limitada
> "Ve a https://sqasa.co/. Haz click *únicamente* en el enlace 'Servicios'. Verifica que la URL cambie correctamente y que el título de la página sea 'Nuestros Servicios'. No navegues a ninguna otra página."

---

## 🛠️ Mejores Prácticas Enterprise
1. **Divide y Vencerás (Micro-Missions):** En lugar de enviar un solo prompt gigante y costoso para probar toda la aplicación, ejecuta múltiples misiones por separado en el Mission Control (Misión 1: Login, Misión 2: Formulario, Misión 3: Menú).
2. **Rutas URL Directas:** Si necesitas probar el carrito de compras, no le digas al agente "Busca un producto y mételo al carrito". Dile: "Navega a `/producto/1`, haz click en agregar y ve a `/carrito`". Esto ahorra miles de tokens en búsquedas visuales innecesarias.
3. **Evita Palabras Absolutas:** Palabras de cuantificación masiva como *"Todos", "Cualquier", "Explora", o "Revisa completo"* son letales para agentes de QA. Desencadenan un comportamiento voraz en el DOM. Sustitúyelas por objetivos singulares.
