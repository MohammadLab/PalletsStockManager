# Orora Pallets Management System

A web-based inventory management system for tracking pallet movements and generating cost reports.

## Features

- Real-time inventory tracking
- Import/Export management
- Monthly movement history
- Automated cost calculations
- Statistical reporting
- Modern, responsive user interface

## Prerequisites

- Python 3.8 or higher
- Flask web framework
- Pandas library
- Modern web browser

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd orora-pallets
```

2. Install required Python packages:
```bash
pip install flask pandas
```

3. Ensure the data directory exists with required files:
```bash
mkdir -p data
```

## File Structure

```
orora-pallets/
├── app.py                 # Main Flask application
├── data/
│   ├── products.csv       # Product database
│   ├── inventory.json     # Current inventory state
│   └── movement_history.json  # Movement records
├── static/
│   └── css/
│       └── style.css      # Application styling
└── templates/
    ├── inventory.html     # Main inventory interface
    └── reports.html       # Reports interface
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Access the application:
   - Open your web browser
   - Navigate to `http://localhost:5000`

## Features Overview

### Inventory Management
- View current stock levels
- Track pallet movements
- Monitor maximum pallet usage

### Movement Tracking
- Record imports and exports
- View movement history
- Delete incorrect entries

### Reports
- Monthly statistics
- Pallet movement analysis
- Storage cost calculations

## Cost Calculations

The system automatically calculates:
- Storage costs ($7.50 per pallet)
- Movement costs ($4.25 per pallet movement)
- Total monthly charges

## Data Management

- Products are stored in CSV format
- Inventory state is maintained in JSON
- Movement history is tracked chronologically

## Browser Compatibility

Tested and optimized for:
- Chrome (latest)
- Firefox (latest)
- Edge (latest)
- Safari (latest)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here]

## Support

For support and questions, please [create an issue](repository-issues-url) or contact the development team.
