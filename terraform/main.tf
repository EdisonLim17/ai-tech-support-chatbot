module "database" {
  source = "./modules/database"
}

module "compute" {
  source = "./modules/compute"
}

module "ai" {
  source = "./modules/ai"
}

module "api" {
  source = "./modules/api"
}

module "monitoring" {
  source = "./modules/monitoring"
}