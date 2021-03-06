import pathlib
import numpy as np

import torch
import torch.utils.data

import torchvision
import torchvision.models
import torchvision.transforms

import augmentations
import transforms


class Dataset:
    def __init__(self, config):
        self.config = config
        dataset_rootdir = pathlib.Path('~/.torchvision/datasets').expanduser()
        
        if self.config['dataset'] == 'K49':
            self.dataset_dir = pathlib.Path('~/data/Kuzushiji/Kuzushiji-49').expanduser()
        else:
            self.dataset_dir = dataset_rootdir / config['dataset']

        self._train_transforms = []
        self.train_transform = self._get_train_transform()
        self.test_transform = self._get_test_transform()

    def get_datasets(self):
        if self.config['dataset'] in ['K49']:
            train_dataset = torchvision.datasets.ImageFolder(
                self.dataset_dir / 'train',
                transform=self.train_transform)
            test_dataset = torchvision.datasets.ImageFolder(
                self.dataset_dir / 'test',
                transform=self.test_transform)
        else:
            train_dataset = getattr(torchvision.datasets, self.config['dataset'])(
                self.dataset_dir,
                train=True,
                transform=self.train_transform,
                download=True)
            test_dataset = getattr(torchvision.datasets, self.config['dataset'])(
                self.dataset_dir,
                train=False,
                transform=self.test_transform,
                download=True)
        return train_dataset, test_dataset

    def _add_random_crop(self):
        transform = torchvision.transforms.RandomCrop(
            self.size, padding=self.config['random_crop_padding'])
        self._train_transforms.append(transform)

    def _add_horizontal_flip(self):
        self._train_transforms.append(
            torchvision.transforms.RandomHorizontalFlip())

    def _add_normalization(self):
        self._train_transforms.append(
            torchvision.transforms.Normalize(self.mean, self.std))

    def _add_normalization_custom(self):
        self._train_transforms.append(
            transforms.Normalize(self.mean, self.std))

    def _add_to_tensor(self):
        self._train_transforms.append(torchvision.transforms.ToTensor())

    def _add_to_tensor_custom(self):
        self._train_transforms.append(transforms.ToTensor())

    def _add_random_erasing(self):
        transform = augmentations.random_erasing.RandomErasing(
            self.config['random_erasing_prob'],
            self.config['random_erasing_area_ratio_range'],
            self.config['random_erasing_min_aspect_ratio'],
            self.config['random_erasing_max_attempt'])
        self._train_transforms.append(transform)

    def _add_cutout(self):
        transform = augmentations.cutout.Cutout(self.config['cutout_size'],
                                                self.config['cutout_prob'],
                                                self.config['cutout_inside'])
        self._train_transforms.append(transform)

    def _add_dual_cutout(self):
        transform = augmentations.cutout.DualCutout(
            self.config['cutout_size'], self.config['cutout_prob'],
            self.config['cutout_inside'])
        self._train_transforms.append(transform)

    def _add_grayscale(self):
        self._train_transforms.append(torchvision.transforms.Grayscale(1))

    def _add_np2pil(self):
        self._train_transforms.append(transforms.Np2pil())

    def _get_train_transform(self):
        if self.config['use_random_crop']:
            self._add_random_crop()
        if self.config['use_horizontal_flip']:
            self._add_horizontal_flip()        
        if self.config['use_random_erasing']:
            self._add_random_erasing()
        if self.config['use_cutout']:
            self._add_cutout()
        elif self.config['use_dual_cutout']:
            self._add_dual_cutout()

        if self.config['dataset'] in ['K49']:
            self._add_np2pil()
            self._add_grayscale()        
            self._add_to_tensor() 
            self._add_normalization()

        self._add_normalization_custom()

        # added for tubify
        if self.config['tubify'] is True:
            self._add_train_tubify()

        self._add_to_tensor_custom()

        return torchvision.transforms.Compose(self._train_transforms)

    def _get_test_transform(self):
        if self.config['dataset'] in ['K49']:
            transform = torchvision.transforms.Compose([ 
                torchvision.transforms.Grayscale(1),                
                torchvision.transforms.ToTensor(),
                torchvision.transforms.Normalize(self.mean, self.std)
            ])
        if self.config['tubify'] is True:
                transform = torchvision.transforms.Compose([
                    transforms.Normalize(self.mean, self.std),
                    Tubify(),
                    transforms.ToTensor(),
                ])
        else:
            transform = torchvision.transforms.Compose([
                transforms.Normalize(self.mean, self.std),
                transforms.ToTensor(),
            ])
        return transform

    # added for tubify
    def _add_train_tubify(self):
        self._train_transforms.append(Tubify())

    # added for tubify
    def _add_test_tubify(self):
        self._test_transforms.append(Tubify())


# added for tubify
class Tubify():

    def __init__(self, d=6) -> None:
        super().__init__()
        self.d = d

    def __call__(self, img):

        img3d = []
        for k in range(self.d):
            mu = np.exp(-(1 / self.d) * (k - (self.d / 2)) ** 2)
            img3d.append(img * mu)

        new_img = np.expand_dims(np.array(img3d), axis=0)

        return new_img


class CIFAR(Dataset):
    def __init__(self, config):
        self.size = 32
        if config['dataset'] == 'CIFAR10':
            self.mean = np.array([0.4914, 0.4822, 0.4465])
            self.std = np.array([0.2470, 0.2435, 0.2616])
        elif config['dataset'] == 'CIFAR100':
            self.mean = np.array([0.5071, 0.4865, 0.4409])
            self.std = np.array([0.2673, 0.2564, 0.2762])
        super(CIFAR, self).__init__(config)


class MNIST(Dataset):
    def __init__(self, config):
        self.size = 28
        if config['dataset'] == 'MNIST':
            self.mean = np.array([0.1307])
            self.std = np.array([0.3081])
        elif config['dataset'] == 'FashionMNIST':
            self.mean = np.array([0.2860])
            self.std = np.array([0.3530])
        elif config['dataset'] == 'KMNIST':
            self.mean = np.array([0.1904])
            self.std = np.array([0.3475])
        elif config['dataset'] == 'K49':
            self.mean = np.array([0.1904])
            self.std = np.array([0.3475])
        super(MNIST, self).__init__(config)


def worker_init_fn(worker_id):
    np.random.seed(np.random.get_state()[1][0] + worker_id)


def get_loader(config):
    batch_size = config['batch_size']
    num_workers = config['num_workers']
    use_gpu = config['use_gpu']

    dataset_name = config['dataset']
    assert dataset_name in [
        'CIFAR10', 'CIFAR100', 'MNIST', 'FashionMNIST', 'KMNIST', 'K49'
    ]

    if dataset_name in ['CIFAR10', 'CIFAR100']:
        dataset = CIFAR(config)
    elif dataset_name in ['MNIST', 'FashionMNIST', 'KMNIST', 'K49']:
        dataset = MNIST(config)

    train_dataset, test_dataset = dataset.get_datasets()

    # num_workers = 0

    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=use_gpu,
        drop_last=True,
        worker_init_fn=worker_init_fn,
    )
    test_loader = torch.utils.data.DataLoader(
        test_dataset,
        batch_size=batch_size,
        num_workers=num_workers,
        shuffle=False,
        pin_memory=use_gpu,
        drop_last=False,
    )
    return train_loader, test_loader
